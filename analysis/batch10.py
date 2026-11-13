"""Batch 10 (13 Nov 2026). Rules and pass marks: analysis/BATCH10_PREREG.md (committed before this file ran)."""

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




import gzip, glob, bisect, datetime as dt
from zoneinfo import ZoneInfo
NYZ = ZoneInfo('America/New_York')
trades = P.book(1.0); base = build('NQ', 'vxn.csv', 'vxn', trades); dl = base['dl']
first = min(t['date'] for t in trades); days = [d for d in dl[1:] if max(LO, first) <= d <= HI]
core = {d: base['w_fix'][d] * base['ret_fix'][d] + base['f_fix'].get(d, 0.0) for d in dl[1:]}
def net(t): return t.get('w', 1.0) * (t['gross'] - t['cost'])
def pkg(keep=lambda t: True, w=lambda d: 1.0):
    R = collections.defaultdict(float)
    for t in trades:
        if keep(t): R[t['date']] += net(t)
    return [core[d] + 0.5 * risk * w(d) * R.get(d, 0.0) + base['tb'][d] for d in days]

# ---- G1: S&P confirmation at entry
pos = {}
for S in ('NQ', 'ES'):
    T, O, H, L, C, n, mins, cdays, wd = c.prep(S); D, _, atr = c.daily(S)
    pos[S] = dict(C=C, D=D, atr=atr, ix={d: {mins[i]: i for i in D[d]['r']} for d in D})
def confirmed(t):
    if t['strat'] == 'expiry' or t['sym'] != 'NQ': return True
    d, m = t['date'], t['entry_min'] - 1; N, E = pos['NQ'], pos['ES']
    if d not in E['D'] or d not in E['atr'] or d not in N['atr'] or m not in E['ix'][d] or m not in N['ix'][d]: return True
    s = 1 if t['side'] in (1, 'long') else -1
    mn = s * (N['C'][N['ix'][d][m]] - N['D'][d]['o']) / N['atr'][d]; me = s * (E['C'][E['ix'][d][m]] - E['D'][d]['o']) / E['atr'][d]
    return me > 0 and me >= 0.5 * mn
# ---- G2 / G3: read the raw Nasdaq minutes for the 08:29, 08:34 closes and 04:00-09:29 volume
dirn = os.path.join(ROOT, 'data', 'databento' if ERA == 'databento' else ERA); c829, c834, pv = {}, {}, collections.defaultdict(float); off = {}
for f in sorted(glob.glob(os.path.join(dirn, 'NQ_*.csv.gz'))):
    with gzip.open(f, 'rt') as fh:
        for r in csv.DictReader(fh):
            ts = r['ts_event']; dk = ts[:13]
            if dk not in off:
                u = dt.datetime(int(ts[:4]), int(ts[5:7]), int(ts[8:10]), int(ts[11:13]), tzinfo=dt.timezone.utc).astimezone(NYZ); off[dk] = (u.date().isoformat(), u.hour)
            d, hr = off[dk]; m = hr * 60 + int(ts[14:16])
            if 240 <= m < 570: pv[d] += float(r['volume'] or 0)
            if m == 509: c829[d] = float(r['close'])
            elif m == 514: c834[d] = float(r['close'])
shock = {d: abs(c834[d] / c829[d] - 1) for d in c829 if d in c834}
def thirds(src):
    out = {}; ks = [d for d in dl if d in src]
    for i, d in enumerate(ks):
        h = sorted(src[x] for x in ks[max(0, i - 252):i])
        if len(h) < 60: out[d] = 1.0; continue
        out[d] = 0.5 if src[d] <= h[len(h) // 3] else (1.5 if src[d] > h[2 * len(h) // 3] else 1.0)
    return out
W2, W3 = thirds(shock), thirds(dict(pv))
SER = {'package baseline': pkg(), 'G1 S&P confirmation': pkg(keep=confirmed), 'G2 8:30 news shock': pkg(w=lambda d: W2.get(d, 1.0)), 'G3 pre-market volume': pkg(w=lambda d: W3.get(d, 1.0))}
hist_ = {k: metrics(v) for k, v in SER.items()}; bt = boot(SER); b0, bb = hist_['package baseline'], bt['package baseline']
def verdict(nm):
    h, b = hist_[nm], bt[nm]
    return 'PASS' if (h['cagr_pct'] > b0['cagr_pct'] and h['sortino'] > b0['sortino'] and h['worst_drop_pct'] >= b0['worst_drop_pct'] - 1
                      and b['chance_drop_worse_than_35_pct'] <= bb['chance_drop_worse_than_35_pct'] + 1) else 'FAIL'
ds = set(days); tin = [t for t in trades if t['date'] in ds and t['strat'] != 'expiry']
def grp(ts): g = [net(t) for t in ts]; return dict(trades=len(g), avg_R=round(sum(g) / len(g), 3) if g else None, total_R=round(sum(g), 1))
Rd = collections.defaultdict(float)
for t in trades: Rd[t['date']] += net(t)
def byw(W): return {str(k): dict(days=sum(1 for d in days if W.get(d, 1.0) == k), avg_rule_R_per_day=round(sum(Rd.get(d, 0.0) for d in days if W.get(d, 1.0) == k) / max(1, sum(1 for d in days if W.get(d, 1.0) == k)), 3)) for k in (0.5, 1.0, 1.5)}
diag = dict(G1=dict(kept=grp([t for t in tin if confirmed(t)]), removed=grp([t for t in tin if not confirmed(t)])), G2=byw(W2), G3=byw(W3))
out = dict(era=ERA, range=[days[0], days[-1]], verdict_this_era={k: verdict(k) for k in list(SER)[1:]}, history=hist_, bootstrap=bt, diagnostics=diag)
json.dump(out, open(os.path.join(ROOT, 'analysis', f'batch10_{ERA}.json'), 'w'), indent=1)
print(out['verdict_this_era']); [print(k, v, bt[k]['chance_drop_worse_than_35_pct']) for k, v in hist_.items()]; print(json.dumps(diag))
