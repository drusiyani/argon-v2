"""Batch 24 step 1 (run once per era): G1/G2/G4/G5 skip flags and each book trade's friction-free R, keyed by
(date, rule, variant, entry minute). Saved to analysis/_cache/ for batch24.py. See BATCH24_PREREG.md."""

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




import bisect, math, statistics, pickle
kw = P.CONFIG['strategies']; RULES = ('quantlab', 'noiseband', 'atrband')
trades = P.book(1.0); key = lambda t: (t['date'], t['strat'], t['variant'], t['entry_min'])
NB0, _ = c.nb_load('NQ'); NB = {d: {b[0]: b for b in v} for d, v in NB0.items()}; nk = sorted(NB); nki = {d: i for i, d in enumerate(nk)}   # per-day list -> dict by minute (fixed after a first run gave all-zero flags; no results were seen); nki = {d: i for i, d in enumerate(nk)}
D, dl, atr = c.daily('NQ'); pos = {d: k for k, d in enumerate(dl)}
def bars5(d):
    B = NB[d]; out = []
    for s in range(570, 960, 5):
        bb = [B[m] for m in range(s, s + 5) if m in B]
        if bb: out.append((s, bb[0][1], max(b[2] for b in bb), min(b[3] for b in bb), bb[-1][4], sum(b[5] for b in bb)))
    return out
B5 = {d: bars5(d) for d in nk}
first = {d: B5[d][0] for d in nk if B5[d] and B5[d][0][0] == 570}
def close_at(d, m):                       # close of the 1-minute bar at minute m (or the last one before it)
    B = NB[d]
    for x in range(m, 569, -1):
        if x in B: return B[x][4]
    return None
# ---- G1
def g1(t):
    d = t['date']; i = nki.get(d)
    if i is None: return False
    if t['strat'] == 'quantlab':
        if d not in first: return False
        prev = [first[q] for q in nk[max(0, i - 40):i] if q in first][-20:]
        if len(prev) < 20: return False
        f = first[d]; return (f[2] - f[3]) > 1.5 * statistics.mean(p[2] - p[3] for p in prev)
    tm = t['entry_min'] - 1; B = NB[d]; bb = [B[m] for m in range(tm - 4, tm + 1) if m in B]
    if not bb: return False
    rng = max(b[2] for b in bb) - min(b[3] for b in bb)
    hist = [b for b in B5[d] if b[0] + 5 <= tm - 4]
    k = i - 1
    while len(hist) < 20 and k >= 0: hist = B5[nk[k]] + hist; k -= 1
    hist = hist[-20:]
    if len(hist) < 20: return False
    return rng > 1.5 * statistics.mean(b[2] - b[3] for b in hist)
# ---- G2
F = {}
for d in nk:
    k = pos.get(d)
    if k is None or k == 0 or d not in first: continue
    o = first[d][1]; F[d] = dict(f1=abs(o - D[dl[k - 1]]['c']) / D[dl[k - 1]]['c'], vol=first[d][5], c935=first[d][4], c1000=close_at(d, 599), o=o)
fd = [d for d in nk if d in F]
for i, d in enumerate(fd):
    pv = [F[q]['vol'] for q in fd[max(0, i - 20):i]]; F[d]['f2'] = F[d]['vol'] / statistics.mean(pv) if len(pv) == 20 and statistics.mean(pv) > 0 else None
def pct667(vals): s = sorted(vals); return s[int(0.667 * (len(s) - 1))]
TH = {}
hist = {'f1': [], 'f2': [], 'f3a': [], 'f3b': []}
for d in fd:
    f = F[d]; f['f3a'] = abs(f['c935'] - f['o']) / f['o']; f['f3b'] = abs(f['c1000'] - f['o']) / f['o'] if f['c1000'] else None
    if len(hist['f1']) >= 60 and len(hist['f2']) >= 60: TH[d] = {k_: pct667(v) for k_, v in hist.items() if len(v) >= 60}
    for k_ in hist:
        if f.get(k_) is not None: hist[k_].append(f[k_])
def g2(t):
    d = t['date']; f = F.get(d); th = TH.get(d)
    if not f or not th or f.get('f2') is None or 'f3a' not in th: return False
    late = t['entry_min'] >= 600; f3 = f['f3b'] if late else f['f3a']; t3 = th.get('f3b') if late else th['f3a']
    if f3 is None or t3 is None: return False
    if not (f['f1'] > th['f1'] and f['f2'] > th['f2'] and f3 > t3): return False
    px = f['c1000'] if late else f['c935']; open_dir = 1 if px > f['o'] else -1; side = 1 if t['side'] in (1, 'long') else -1
    return side == open_dir
# ---- G4
V = csvmap('vxn.csv', 'vxn'); vk = sorted(V)
def g4(t):
    if t['strat'] == 'quantlab': return False
    d = t['date']; k = pos.get(d)
    if k is None or k < 21: return False
    v, _ = lastbefore(V, vk, d)
    if not v: return False
    rets = [math.log(D[dl[j]]['c'] / D[dl[j - 1]]['c']) for j in range(k - 20, k)]; rv = statistics.pstdev(rets) * math.sqrt(252) * 100
    gtbr = (v / 100) / math.sqrt(252); px = close_at(d, t['entry_min'] - 1)
    if px is None or d not in first: return False
    move = abs(px - first[d][1]) / first[d][1]
    return (move / gtbr < 0.5) and (v > rv)
# ---- G5
def g5(t):
    if t['strat'] != 'quantlab' or t['date'] not in first: return False
    _, o, h, l, cl, _ = first[t['date']]
    if h <= l: return False
    side = 1 if t['side'] in (1, 'long') else -1
    return ((h - cl) / (h - l) > 0.5) if side == 1 else ((cl - l) / (h - l) > 0.5)
FLAGS = {}
for t in trades:
    if t['strat'] not in RULES or t['sym'] != 'NQ': continue
    FLAGS[key(t)] = dict(G1=g1(t), G2=g2(t), G4=g4(t), G5=g5(t))
# ---- friction-free R for every book trade (batch 22's method)
raw = P.raw(); SL0, C0 = dict(c.SL), dict(c.COST); c.SL = {k_: 0.0 for k_ in SL0}; c.COST = {k_: 0.0 for k_ in C0}
FREE = dict(quantlab=c.quantlab('NQ', **kw['quantlab']), noiseband=c.noiseband('NQ', **kw['noiseband']), atrband=c.atrband('NQ', **kw['atrband']))
c.SL, c.COST = SL0, C0
fk = lambda t: (t['date'], t['variant'], t['entry_min'])
FM = {r: {fk(t): t['gross'] * t['risk_pts'] for t in FREE[r]} for r in RULES}
FREE_R = {}
for t in trades:
    if t['strat'] in RULES:
        f = FM[t['strat']].get(fk(t))
        if f is not None: FREE_R[key(t)] = f / t['risk_pts']
os.makedirs(os.path.join(ROOT, 'analysis', '_cache'), exist_ok=True)
pickle.dump(dict(era=ERA, flags=FLAGS, free_R=FREE_R), open(os.path.join(ROOT, 'analysis', '_cache', f'batch24_{ERA}.pkl'), 'wb'))
cnt = {g: sum(v[g] for v in FLAGS.values()) for g in ('G1', 'G2', 'G4', 'G5')}
print('ok', len(FLAGS), len(FREE_R), cnt)
