"""Batch 18 (14 Nov 2026). Rules and marks: analysis/BATCH18_PREREG.md (committed before this file ran).
Needs analysis/_cache/squeezemetrics_DIX.csv (squeezemetrics.com/monitor/static/DIX.csv)."""

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
# ---------- Q: QuantLab second chance
def reentries(raw_ql, s='NQ'):
    T, O, H, L, C, n, mins, days, wd = c.prep(s); b5, EMA, atr5, datr = c.bars5(s, 12); TK = c.SL[s]; V = c.ql_variants()
    start = {}
    for j, b in enumerate(b5):
        if mins[b[1]] == 595: start[days[b[1]]] = j          # the 9:55-10:00 bar
    out = []
    for t in raw_ql:
        if not (t['exit_min'] < 585 and t['gross'] < 0): continue      # stopped out before 9:45 (an EMA exit cannot happen before 9:45)
        d = t['date']; j = start.get(d)
        if j is None or j + 1 >= len(b5) or days[b5[j + 1][1]] != d or not datr.get(d): continue
        side = t['side']
        if not ((b5[j][6] > EMA[j]) if side == 1 else (b5[j][6] < EMA[j])): continue
        stk, trk = V[t['variant']]; ej = j + 1; ei = b5[ej][1]; entry = O[ei] + side * 2 * TK
        stop = entry - side * 0.10 * datr[d]; risk = (entry - stop) * side
        if risk <= 0: continue
        stp = stop; best = entry; res = None; xm = None
        for jj in range(ej, len(b5)):
            bb = b5[jj]
            if days[bb[1]] != d: break
            for i in range(bb[1], bb[2] + 1):
                m = mins[i]
                if m >= 955: res = (C[i] - entry) * side; xm = m; break
                if (L[i] <= stp) if side == 1 else (H[i] >= stp): res = (stp - side * TK - entry) * side; xm = m; break
            if res is not None: break
            best = max(best, bb[4]) if side == 1 else min(best, bb[5])
            if trk == 'ema':
                if (bb[6] < EMA[jj]) if side == 1 else (bb[6] > EMA[jj]):
                    nxt = bb[2] + 1; res = ((O[nxt] if nxt < n else bb[6]) - side * TK - entry) * side; xm = mins[min(nxt, n - 1)]; break
            else:
                k = float(trk[2:]); ts = best - side * k * atr5[jj]; stp = max(stp, ts) if side == 1 else min(stp, ts)
        if res is None: continue
        r = c.trade('quantlab', s, d, t['variant'], side, mins[ei], xm, risk, res, entry); r['reentry'] = True; out.append(r)
    return out
raw = P.raw(); base_ql = list(raw['quantlab']); RE = reentries(base_ql)
trades0 = P.book(1.0)
raw['quantlab'] = base_ql + RE; tradesQ = P.book(1.0); raw['quantlab'] = base_ql
base = build('NQ', 'vxn.csv', 'vxn', trades0); dl = base['dl']
first = min(t['date'] for t in trades0); days = [d for d in dl[1:] if max(LO, first) <= d <= HI]
core = {d: base['w_fix'][d] * base['ret_fix'][d] + base['f_fix'].get(d, 0.0) for d in dl[1:]}
def net(t): return t.get('w', 1.0) * (t['gross'] - t['cost'])
def mom(t): return t['strat'] != 'expiry' and t['sym'] == 'NQ'
def series(tr, wday=None):
    R = collections.defaultdict(float)
    for t in tr: R[t['date']] += (wday(t['date']) if (wday and mom(t)) else 1.0) * net(t)
    return [core[d] + 0.5 * risk * R.get(d, 0.0) + base['tb'][d] for d in days]
# ---------- G: SqueezeMetrics GEX regime
GX = {}
for r in csv.DictReader(open(os.path.join(ROOT, 'analysis', '_cache', 'squeezemetrics_DIX.csv'))):
    try: GX[r['date']] = float(r['gex'])
    except ValueError: pass
gk = sorted(GX)
def regime(d):
    i = bisect.bisect_left(gk, d) - 1
    if i < 126: return None
    h = sorted(GX[k] for k in gk[max(0, i - 252):i]); return 'low' if GX[gk[i]] < h[len(h) // 2] else 'high'
REG = {d: regime(d) for d in dl}
G1 = lambda d: 1.0 if REG.get(d) is None else (1.0 if REG[d] == 'low' else 0.0)
G2 = lambda d: 1.0 if REG.get(d) is None else (1.5 if REG[d] == 'low' else 0.5)
IDX = [base['ret_fix'][d] for d in days]; LIM = dict(drop=metrics(IDX)['worst_drop_pct'], boot=boot({'i': IDX})['i']['chance_drop_worse_than_35_pct'])
SER = {'package baseline': series(trades0), 'Q QuantLab second chance': series(tradesQ), 'G1 low-gamma days only': series(trades0, G1), 'G2 gamma reallocation': series(trades0, G2)}
hist_ = {k: metrics(v) for k, v in SER.items()}; bt = boot(SER); b0, bb = hist_['package baseline'], bt['package baseline']
def marks(nm):
    h, b = hist_[nm], bt[nm]['chance_drop_worse_than_35_pct']; better = h['cagr_pct'] > b0['cagr_pct'] and h['sortino'] > b0['sortino']
    return dict(strict=bool(better and h['worst_drop_pct'] >= b0['worst_drop_pct'] - 1 and b <= bb['chance_drop_worse_than_35_pct'] + 1),
                growth=bool(better and h['worst_drop_pct'] >= b0['worst_drop_pct'] - 5 and h['worst_drop_pct'] >= LIM['drop'] and b <= LIM['boot']))
ds = set(days); PER = (('2010-17', '2010', '2018'), ('2018-20', '2018', '2021'), ('2021-25', '2021', '2026'), ('2026', '2026', '2027'))
re_in = [t for t in RE if t['date'] in ds]
def grp(L): g = [t['gross'] - t['cost'] for t in L]; return dict(trades=len(g), avg_R=round(sum(g) / len(g), 3) if g else None, total_R=round(sum(g), 1))
diagQ = {lab: grp([t for t in re_in if a <= t['date'] < b]) for lab, a, b in PER}
diagQ['picked_into_book'] = sum(1 for t in tradesQ if t.get('reentry') and t['date'] in ds)
Rd = collections.defaultdict(float)
for t in trades0:
    if mom(t): Rd[t['date']] += net(t)
diagG = {}
for lab, a, b in (('2011-17', '2011', '2018'), ('2018-20', '2018', '2021'), ('2021-26', '2021', '2027')):
    for rg in ('low', 'high'):
        dd = [d for d in days if a <= d < b and REG.get(d) == rg]
        if dd: diagG[f'{lab} {rg}'] = dict(days=len(dd), avg_rules_R_per_day=round(sum(Rd.get(d, 0.0) for d in dd) / len(dd), 3))
out = dict(era=ERA, range=[days[0], days[-1]], limits_index_alone=LIM, history=hist_, bootstrap=bt, marks={k: marks(k) for k in list(SER)[1:]}, diag_reentry=diagQ, diag_gamma=diagG)
json.dump(out, open(os.path.join(ROOT, 'analysis', f'batch18_{ERA}.json'), 'w'), indent=1)
for k, v in hist_.items(): print(f"{k:28s} {v['cagr_pct']:6.1f} {v['sharpe']:5.2f} {v['sortino']:5.2f} {v['worst_drop_pct']:6.1f} {bt[k]['chance_drop_worse_than_35_pct']:5.1f}", out['marks'].get(k, ''))
print('reentry', diagQ); print('gamma', diagG)
