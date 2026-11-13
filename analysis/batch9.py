"""Batch 9 (13 Nov 2026). Rules and pass marks: analysis/BATCH9_PREREG.md (committed before this file ran).
Stage 1 (run once per era): H1-H4 and the day-level file that stage 2 (batch9_ml.py, H5) reads."""

import os, sys, json, math, csv, random, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'engine'))
import portfolio as P
c = P.c
ERA = os.environ.get('ARGON_DATA', 'databento'); risk = P.CONFIG['risk_pct'] / 100; cap = P.CONFIG['cost_cap_R']
LO, HI = (('2021-01-01', '2026-12-31') if ERA == 'databento' else ('2010-07-01', '2020-12-31'))
PC = {'2011-04-27', '2011-06-22', '2011-11-02', '2012-01-25', '2012-04-25', '2012-06-20', '2012-09-13', '2012-12-12'}
def csvmap(fn, col): return {r['date']: float(r[col]) for r in csv.DictReader(open(os.path.join(ROOT, 'analysis', fn)))}
TB = {d: v / 100 / 252 for d, v in csvmap('tbill_dtb3.csv', 'dtb3_pct').items()} if False else None
TB = {r['date']: float(r['dtb3_pct']) / 100 / 252 for r in csv.DictReader(open(os.path.join(ROOT, 'analysis', 'tbill_dtb3.csv')))}

def skipset(S):
    out = {'roll': set(), 'bad': set()}
    for f, k in (('roll', 'roll'), ('bad_days', 'bad')):
        try:
            v = getattr(c, f)(S); v = v.keys() if isinstance(v, dict) else v; out[k] = {x for x in v if isinstance(x, str) and len(x) == 10}
        except Exception: pass
    return out

def lastbefore(src, keys, d):
    import bisect
    i = bisect.bisect_left(keys, d); return (src[keys[i - 1]], i - 1) if i > 0 else (None, -1)

def build(S, volfile, volcol, book_trades):
    D, dl, _ = c.daily(S); T, O, H, L, C, n, mins, days, wd = c.prep(S); sk = skipset(S)
    ret_fix, ret_old = {}, {}
    for k in range(1, len(dl)):
        d, p = dl[k], dl[k - 1]; r = D[d]['c'] / D[p]['c'] - 1
        bad = d in sk['bad'] or p in sk['bad']; roll = d in sk['roll'] or p in sk['roll']
        ret_old[d] = 0.0 if (bad or roll or abs(r) > 0.15) else r
        ret_fix[d] = 0.0 if bad else ((D[d]['c'] / D[d]['o'] - 1) if (roll or abs(r) > 0.15) else r)
    V = csvmap(volfile, volcol); vk = sorted(V); tbk = sorted(TB)
    def volw(d, prev_day):
        v, i = lastbefore(V, vk, prev_day)
        if not v: return 1.0
        h = sorted(V[x] for x in vk[max(0, i - 251):i + 1]); med = h[len(h) // 2] if len(h) >= 60 else v
        return min(1.5, med / v)
    pos = {d: k for k, d in enumerate(dl)}
    w_fix = {dl[k]: volw(dl[k], dl[k - 1]) for k in range(1, len(dl))}            # vol index known before yesterday's close
    w_old = {dl[k]: volw(dl[k], dl[k]) for k in range(1, len(dl))}                # the 11 Nov version (yesterday's close print)
    tb = {d: (lastbefore(TB, tbk, d)[0] or 0.0) for d in dl}
    def fomc(fixed):
        out = {}
        for d in sorted(c.FOMC):
            if d not in pos or pos[d] == 0: continue
            p = dl[pos[d] - 1]
            if d in sk['bad'] or p in sk['bad'] or ((d in sk['roll'] or p in sk['roll']) and not fixed): continue
            lim = 734 if (fixed and d in PC) else 839
            i2 = [i for i in D[d]['r'] if mins[i] <= lim]
            if i2: out[d] = C[i2[-1]] / D[p]['c'] - 1 - c.COST[S] / D[p]['c']
        return out
    f_fix, f_old = fomc(True), fomc(False)
    bk = collections.defaultdict(float); bl = collections.defaultdict(float)
    for t in book_trades:
        x = t.get('w', 1.0) * (t['gross'] - t['cost']); bk[t['date']] += x
        if t['strat'] == 'expiry' or t['side'] in (1, 'long'): bl[t['date']] += x
    return dict(dl=dl, ret_fix=ret_fix, ret_old=ret_old, w_fix=w_fix, w_old=w_old, tb=tb, f_fix=f_fix, f_old=f_old, bk=bk, bl=bl)

def metrics(x):
    eq, peak, dd = 1.0, 1.0, 0.0
    for v in x: eq *= 1 + v; peak = max(peak, eq); dd = min(dd, eq / peak - 1)
    n_ = len(x); m = sum(x) / n_; s = math.sqrt(sum((v - m) ** 2 for v in x) / (n_ - 1)) or 1e-12
    dn = math.sqrt(sum(min(0.0, v) ** 2 for v in x) / n_) or 1e-12
    return dict(final_usd=round(100000 * eq), cagr_pct=round(100 * (max(eq, 1e-9) ** (252 / n_) - 1), 1), sharpe=round(m / s * math.sqrt(252), 2),
                sortino=round(m / dn * math.sqrt(252), 2), worst_drop_pct=round(100 * dd, 1))

def boot(SER, draws=1000, B=63, seed=20261111):
    rng = random.Random(seed); N = len(next(iter(SER.values()))); res = {k: [] for k in SER}
    for _ in range(draws):
        idx = []
        while len(idx) < N: st = rng.randrange(0, N - B); idx.extend(range(st, st + B))
        idx = idx[:N]
        for k, v in SER.items():
            eq, peak, dd = 1.0, 1.0, 0.0
            for i in idx: eq *= 1 + v[i]; peak = max(peak, eq); dd = min(dd, eq / peak - 1)
            res[k].append((max(eq, 1e-9) ** (252 / N) - 1, dd))
    out = {}
    for k, v in res.items():
        cg = sorted(a for a, _ in v); dd = [b for _, b in v]
        out[k] = dict(median_cagr_pct=round(100 * cg[len(cg) // 2], 1), bad_case_cagr_pct_5th=round(100 * cg[len(cg) // 20], 1),
                      chance_losing_money_pct=round(100 * sum(a < 0 for a, _ in v) / draws, 1),
                      chance_drop_worse_than_35_pct=round(100 * sum(b < -.35 for b in dd) / draws, 1))
    return out




import bisect, statistics
trades = P.book(1.0); base = build('NQ', 'vxn.csv', 'vxn', trades); dl = base['dl']
R0 = collections.defaultdict(float)
for t in trades: R0[t['date']] += t.get('w', 1.0) * (t['gross'] - t['cost'])
first = min(t['date'] for t in trades); days = [d for d in dl[1:] if max(LO, first) <= d <= HI]
D, _, atr = c.daily('NQ'); sk = skipset('NQ'); pos = {d: k for k, d in enumerate(dl)}
V = csvmap('vxn.csv', 'vxn'); vk = sorted(V)
def vratio(k):                                   # VXN / its trailing-252 median, read as the core reads it (one day early)
    v, i = lastbefore(V, vk, dl[k - 1])
    if not v: return 1.0, None
    h = sorted(V[x] for x in vk[max(0, i - 251):i + 1]); med = h[len(h) // 2] if len(h) >= 60 else v
    v5 = V[vk[i - 5]] if i >= 5 else v
    return v / med, v / v5 - 1
VR = {dl[k]: vratio(k) for k in range(1, len(dl))}
core = {d: base['w_fix'][d] * base['ret_fix'][d] + base['f_fix'].get(d, 0.0) for d in dl[1:]}
def pkg(rule_w=lambda d: 1.0, extra=None, k=None):
    out = []
    for d in days:
        x = core[d] + 0.5 * risk * rule_w(d) * R0.get(d, 0.0) + (extra.get(d, 0.0) if extra else 0.0)
        out.append((k[d] if k else 1.0) * x + base['tb'][d])
    return out
BASE = pkg()
# H1 regime tilt
H1 = pkg(rule_w=lambda d: min(1.5, VR[d][0]))
# H2 overnight after a down day: extra 0.5x from d's close to the next 9:30 open, booked on the next day
ON = {}; n_on = 0
for k in range(1, len(dl) - 1):
    d, nx = dl[k], dl[k + 1]
    if D[d]['c'] >= D[d]['o']: continue
    if {d, nx} & (sk['roll'] | sk['bad']): continue
    r = D[nx]['o'] / D[d]['c'] - 1
    if abs(r) > 0.15: continue
    ON[nx] = 0.5 * (r - c.COST['NQ'] / D[d]['c']); n_on += (nx in set(days))
H2 = pkg(extra=ON)
# H3 volatility-managed package size
allx = {d: core[d] + 0.5 * risk * R0.get(d, 0.0) for d in dl[1:] if d >= first}; ad = sorted(allx); sig = {}; K = {}
for i, d in enumerate(ad):
    if i >= 23: w = [allx[x] for x in ad[i - 23:i - 1]][-21:]; sig[d] = statistics.pstdev(w)     # returns up to two days earlier
    h = [sig[x] for x in ad[max(0, i - 251):i + 1] if x in sig]
    K[d] = min(1.5, statistics.median(h) / sig[d]) if (len(h) >= 60 and sig.get(d)) else 1.0
H3 = pkg(k=K)
# H4 European-session noise band
T, O, Hh, L, C, n, mins, cdays, wd = c.prep('NQ'); byday = collections.defaultdict(list)
for i in range(n):
    if 180 <= mins[i] < 566: byday[cdays[i]].append(i)
hist = collections.deque(maxlen=14); EU = collections.defaultdict(float); eu_tr = []; tk = 0.25; ECOST = 1.25
for d in dl:
    ix = byday.get(d)
    if not ix or mins[ix[0]] > 185 or len(ix) < 300 or d in sk['roll'] | sk['bad']: continue
    P0 = O[ix[0]]; px = {}; last = ix[0]; j = 0   # bug fix before any 2010-20 result was seen: a day whose first bar is 03:01-03:05 has no 03:00 bar
    for m in range(180, 566):
        while j < len(ix) and mins[ix[j]] <= m: last = ix[j]; j += 1
        px[m] = last
    move = {m: abs(C[px[m]] / P0 - 1) for m in range(180, 566)}
    if len(hist) >= 10:
        sg = lambda m: sum(h[m] for h in hist) / len(hist); side = 0; entry = risk_pts = None; ok = True
        nxt_open = lambda m: next((O[i] for i in ix if mins[i] >= m), None)
        for m in list(range(210, 541, 30)) + [565]:
            p = C[px[m - 1]]; s = sg(m - 1); up, dn = P0 * (1 + s), P0 * (1 - s); o = nxt_open(m)
            if o is None: break
            if side and (m == 565 or (p < up if side == 1 else p > dn)):
                eu_tr.append(dict(date=d, gross=(o - entry) * side / risk_pts, cost=ECOST / risk_pts)); side = 0
            if not side and m < 565 and s > 0:
                ns = 1 if p > up else (-1 if p < dn else 0)
                if ns and ECOST / (s * P0) <= cap: side = ns; entry = o + ns * tk; risk_pts = s * P0
    hist.append(move)
for t in eu_tr: EU[t['date']] += 0.5 * risk * (t['gross'] - t['cost'])
H4 = pkg(extra=EU)

SER = {'package baseline': BASE, 'H1 regime tilt': H1, 'H2 overnight after down day': H2, 'H3 vol-managed size': H3, 'H4 European noise band': H4}
hist_ = {k: metrics(v) for k, v in SER.items()}; bt = boot(SER); b0, bb = hist_['package baseline'], bt['package baseline']
def verdict(nm):
    h, b = hist_[nm], bt[nm]
    return 'PASS' if (h['cagr_pct'] > b0['cagr_pct'] and h['sortino'] > b0['sortino'] and h['worst_drop_pct'] >= b0['worst_drop_pct'] - 1
                      and b['chance_drop_worse_than_35_pct'] <= bb['chance_drop_worse_than_35_pct'] + 1) else 'FAIL'
ds = set(days); eu_in = [t for t in eu_tr if t['date'] in ds]; g = [t['gross'] - t['cost'] for t in eu_in]
diag = dict(H1_avg_rule_weight=round(sum(min(1.5, VR[d][0]) for d in days) / len(days), 2),
            H2_nights=n_on, H2_total_pct=round(100 * sum(ON.get(d, 0) for d in days), 1),
            H3_avg_k=round(sum(K[d] for d in days) / len(days), 2),
            H4=dict(trades=len(g), total_R=round(sum(g), 1), avg_R=round(sum(g) / len(g), 3) if g else None, win_pct=round(100 * sum(x > 0 for x in g) / len(g), 1) if g else None))
out = dict(era=ERA, range=[days[0], days[-1]], verdict_this_era={k: verdict(k) for k in list(SER)[1:]}, history=hist_, bootstrap=bt, diagnostics=diag)
json.dump(out, open(os.path.join(ROOT, 'analysis', f'batch9_{ERA}.json'), 'w'), indent=1)
# day-level file for stage 2 (H5): features known by 9:30, the rules' R, and the package pieces
rows = []
for d in days:
    k = pos[d]; p = dl[k - 1]
    if d not in atr or p not in atr or k < 22: f = None
    else:
        r20 = 1.0
        for x in dl[k - 20:k]: r20 *= 1 + base['ret_fix'].get(x, 0.0)
        f = [VR[d][0], VR[d][1] or 0.0, abs(D[d]['o'] - D[p]['c']) / atr[d], abs(D[p]['c'] - D[p]['o']) / atr[p], r20 - 1, sum(R0.get(x, 0.0) for x in dl[k - 5:k])]
    rows.append(dict(date=d, f=f, R=R0.get(d, 0.0), core=core[d], tb=base['tb'][d]))
json.dump(dict(era=ERA, risk=risk, rows=rows), open(os.path.join(ROOT, 'analysis', f'batch9_days_{ERA}.json'), 'w'))
print(json.dumps(dict(v=out['verdict_this_era'], hist=hist_, boot={k: x['chance_drop_worse_than_35_pct'] for k, x in bt.items()}, diag=diag), indent=1))
