"""Batch 13 (14 Nov 2026). Rules and pass marks: analysis/BATCH13_PREREG.md (committed before this file ran).
Step 2: reads analysis/_cache/batch13_{era}.pkl written by batch13_dump.py."""
import os, json, math, random, pickle, collections, statistics, datetime as dt
import numpy as np
A = os.path.dirname(os.path.abspath(__file__)); ERAS = ('databento', 'lockbox2010')
Z = {e: pickle.load(open(f'{A}/_cache/batch13_{e}.pkl', 'rb')) for e in ERAS}
def metrics(x):
    eq, peak, dd = 1.0, 1.0, 0.0
    for v in x: eq *= 1 + v; peak = max(peak, eq); dd = min(dd, eq / peak - 1)
    n_ = len(x); m = sum(x) / n_; s = math.sqrt(sum((v - m) ** 2 for v in x) / (n_ - 1)) or 1e-12
    dn = math.sqrt(sum(min(0.0, v) ** 2 for v in x) / n_) or 1e-12
    return dict(cagr_pct=round(100 * (max(eq, 1e-9) ** (252 / n_) - 1), 1), sharpe=round(m / s * math.sqrt(252), 2), sortino=round(m / dn * math.sqrt(252), 2), worst_drop_pct=round(100 * dd, 1))
def boot(x, B=63, draws=1000, seed=20261111):
    rng = random.Random(seed); N = len(x); bad = 0
    for _ in range(draws):
        idx = []
        while len(idx) < N: st = rng.randrange(0, N - B); idx.extend(range(st, st + B))
        eq, peak, dd = 1.0, 1.0, 0.0
        for i in idx[:N]: eq *= 1 + x[i]; peak = max(peak, eq); dd = min(dd, eq / peak - 1)
        bad += dd < -.35
    return round(100 * bad / draws, 1)
sg = lambda v: 1 if v > 0 else (-1 if v < 0 else 0); clip = lambda v, a: max(-a, min(a, v))
def net(t): return t.get('w', 1.0) * (t['gross'] - t['cost'])
def mom(t): return t['strat'] != 'expiry' and t['sym'] == 'NQ'
E = {}; ROWS = []; M = {k: {} for k in ('K1', 'M1', 'M2', 'M3')}
for e in ERAS:
    z = Z[e]; dl = z['dl']; pos = {d: k for k, d in enumerate(dl)}; D = z['D']; atr = z['atr']; days = z['days']; ds = set(days)
    tr = [dict(t, id=(e, i)) for i, t in enumerate(z['trades'])]
    YR = collections.defaultdict(float); YN = collections.Counter(); byday = collections.defaultdict(list)
    for t in tr:
        if mom(t): YR[t['date']] += t['gross'] - t['cost']; YN[t['date']] += 1; byday[t['date']].append(t)
    core = {d: z['w'][d] * z['ret'][d] + z['fomc'].get(d, 0.0) for d in dl[1:]}
    for d, L in byday.items():
        L.sort(key=lambda t: t['entry_min']); k = pos.get(d, 0)
        if k == 0: continue
        p = dl[k - 1]; o, h, l, cl = D[d]; po, ph, pl, pc = D[p]
        ql = [x for x in L if x['strat'] == 'quantlab']; qs = (1 if ql[0]['side'] in (1, 'long') else -1) if ql else 0
        for j, t in enumerate(L):
            s = 1 if t['side'] in (1, 'long') else -1; g = (o - pc) * s; y = (pc - po) * s
            M['K1'][t['id']] = 1.5 if g > 0 else (0.5 if g < 0 else 1.0)
            M['M1'][t['id']] = 1.0 if YN[p] == 0 else (1.5 if YR[p] < 0 else (0.5 if YR[p] > 0 else 1.0))
            M['M2'][t['id']] = 0.0 if YR[p] > 2.0 else 1.0
            M['M3'][t['id']] = 1.5 if (g > 0 and y < 0) else (0.5 if (g < 0 and y > 0) else 1.0)
            if d not in ds or d not in atr or p not in atr or k < 22: continue
            a, ap = atr[d], atr[p]; onh, onl, _ = z['on'].get(d, (o, o, o)); cloc = (pc - pl) / (ph - pl) if ph > pl else .5
            sofar = sum(x['gross'] - x['cost'] for x in L[:j] if x['exit_min'] <= t['entry_min'])
            same = sum(1 for x in L[:j] if x['exit_min'] > t['entry_min'] and (1 if x['side'] in (1, 'long') else -1) == s)
            f = [sg(g), abs(o - pc) / a, clip(g / a, 3), clip(y / ap, 3), clip(s * (pc - D[dl[k - 2]][3]) / ap, 3), clip(s * (pc - D[dl[k - 6]][3]) / a / math.sqrt(5), 3),
                 clip(s * (pc - D[dl[k - 21]][3]) / a / math.sqrt(20), 3), (1 if ((o > ph and s == 1) or (o < pl and s == -1)) else (-1 if (o > ph or o < pl) else 0)),
                 s * (2 * cloc - 1), (ph - pl) / ap, clip(YR[p], 5), 1.0 if YN[p] == 0 else 0.0, z['w'][d], s, 1.0 if t['strat'] == 'quantlab' else 0.0,
                 1.0 if t['strat'] == 'noiseband' else 0.0, (t['entry_min'] - 570) / 390, t['risk_pts'] / a, min(same, 2), min(j + 1, 3),
                 0 if (t['strat'] == 'quantlab' or not qs) else qs * s, 1.0 if dt.date.fromisoformat(d).weekday() == 0 else 0.0,
                 s * (2 * (o - onl) / (onh - onl) - 1) if onh > onl else 0.0, clip(sofar, 3)]
            ROWS.append(dict(id=t['id'], date=d, y=t['gross'] - t['cost'], f=f))
    E[e] = dict(z=z, tr=tr, core=core, days=days, ds=ds)
NF = len(ROWS[0]['f']); assert NF == 24
# ---- Part B: walk-forward models (each year fitted on earlier years only)
from sklearn.ensemble import HistGradientBoostingRegressor
ROWS.sort(key=lambda r: r['date']); years = sorted({r['date'][:4] for r in ROWS}); W = {'W1': {}, 'W2': {}}; wf_log = {}
for Y in years:
    trn = [r for r in ROWS if r['date'] < Y]; tst = [r for r in ROWS if r['date'][:4] == Y]
    if len(trn) < 500: continue
    X = np.array([r['f'] for r in trn]); yv = np.array([r['y'] for r in trn]); Xt = np.array([r['f'] for r in tst])
    mu, sd = X.mean(0), X.std(0); sd[sd == 0] = 1; S = np.c_[np.ones(len(X)), (X - mu) / sd]; pen = np.eye(NF + 1) * 100.0; pen[0, 0] = 0
    b = np.linalg.solve(S.T @ S + pen, S.T @ yv); ptr = S @ b; pts = np.c_[np.ones(len(Xt)), (Xt - mu) / sd] @ b
    g = HistGradientBoostingRegressor(max_depth=3, max_iter=200, learning_rate=0.03, min_samples_leaf=100, random_state=0).fit(X, yv); gtr = g.predict(X); gts = g.predict(Xt)
    for nm, a_, b_ in (('W1', ptr, pts), ('W2', gtr, gts)):
        lo, hi = np.quantile(a_, [1 / 3, 2 / 3])
        for r, p in zip(tst, b_): W[nm][r['id']] = 0.5 if p < lo else (1.5 if p > hi else 1.0)
    wf_log[Y] = dict(trained_on=len(trn), sized=len(tst))
# ---- series builders
def series(e, mult=None, k=1.0, volman=False):
    z = E[e]['z']; risk = z['risk']; R = collections.defaultdict(float)
    for t in E[e]['tr']: R[t['date']] += (mult(t) if (mult and mom(t)) else 1.0) * net(t)
    x = {d: E[e]['core'][d] + 0.5 * risk * R.get(d, 0.0) for d in z['dl'][1:]}
    K = {}
    if volman:                                               # H3, exactly as batch 9
        first = min(t['date'] for t in E[e]['tr']); ad = sorted(d for d in x if d >= first); sig = {}
        for i, d in enumerate(ad):
            if i >= 23: sig[d] = statistics.pstdev([x[q] for q in ad[i - 23:i - 1]][-21:])
            h = [sig[q] for q in ad[max(0, i - 251):i + 1] if q in sig]
            K[d] = min(1.5, statistics.median(h) / sig[d]) if (len(h) >= 60 and sig.get(d)) else 1.0
    return [k * K.get(d, 1.0) * x[d] + z['tb'][d] for d in E[e]['days']]
def capped(*ms): return lambda t: min(2.0, math.prod(m.get(t['id'], 1.0) for m in ms))
IDX = {e: [E[e]['z']['ret'][d] for d in E[e]['days']] for e in ERAS}
LIM = {e: dict(drop=metrics(IDX[e])['worst_drop_pct'], boot=boot(IDX[e])) for e in ERAS}
BASE = {e: series(e) for e in ERAS}; B0 = {e: dict(metrics(BASE[e]), boot=boot(BASE[e])) for e in ERAS}
def score(name, build):
    out = {'name': name}
    for e in ERAS:
        x = build(e); h = dict(metrics(x), boot=boot(x)); b = B0[e]; better = h['cagr_pct'] > b['cagr_pct'] and h['sortino'] > b['sortino']
        h['strict'] = bool(better and h['worst_drop_pct'] >= b['worst_drop_pct'] - 1 and h['boot'] <= b['boot'] + 1)
        h['growth'] = bool(better and h['worst_drop_pct'] >= b['worst_drop_pct'] - 5 and h['worst_drop_pct'] >= LIM[e]['drop'] and h['boot'] <= LIM[e]['boot'])
        x125 = build(e, 1.25); h['lev125'] = dict(metrics(x125), boot21=boot(x125, B=21)); h['lev125']['ok'] = bool(h['lev125']['worst_drop_pct'] > -35 and h['lev125']['boot21'] < 20)
        out[e] = h
    out['strict_both'] = out['databento']['strict'] and out['lockbox2010']['strict']; out['growth_both'] = out['databento']['growth'] and out['lockbox2010']['growth']
    out['lev125_both'] = out['databento']['lev125']['ok'] and out['lockbox2010']['lev125']['ok']; return out
mk = lambda *ms, volman=False: (lambda e, k=1.0: series(e, capped(*ms) if ms else None, k, volman))
RES = collections.OrderedDict()
RES['baseline'] = score('package baseline', mk())
for nm in ('K1', 'M1', 'M2', 'M3'): RES[nm] = score(nm + ' (re-scored)', mk(M[nm]))
RES['H3'] = score('H3 vol-managed size (re-scored)', mk(volman=True))
RES['W1'] = score('W1 walk-forward ridge', mk(W['W1'])); RES['W2'] = score('W2 walk-forward boosting', mk(W['W2']))
partsA = [nm for nm in ('M1', 'M2', 'M3') if RES[nm]['growth_both']]
RES['StackA'] = score('Stack A = ' + ' x '.join(partsA), mk(*[M[n] for n in partsA]))
if RES['H3']['growth_both']: RES['StackB'] = score('Stack B = Stack A + H3', mk(*[M[n] for n in partsA], volman=True))
wpick = 'W1' if RES['W1']['growth_both'] else ('W2' if RES['W2']['growth_both'] else None)
if wpick: RES['StackC'] = score(f'Stack C = Stack A x {wpick}', mk(*[M[n] for n in partsA], W[wpick]))
# out-of-sample check of the walk-forward sizes: average R of trades by the size the model gave them
diag = {}
for nm in ('W1', 'W2'):
    for lab, a, b in (('2013-17', '2013', '2018'), ('2018-20', '2018', '2021'), ('2021-26', '2021', '2027')):
        for m in (0.5, 1.0, 1.5):
            v = [r['y'] for r in ROWS if a <= r['date'] < b and W[nm].get(r['id']) == m]
            diag[f'{nm} {lab} x{m}'] = dict(trades=len(v), avg_R=round(sum(v) / len(v), 3) if v else None)
json.dump(dict(limits_index_alone=LIM, baseline=B0, results=RES, walk_forward_years=wf_log, walk_forward_buckets=diag), open(f'{A}/batch13.json', 'w'), indent=1)
print('index limits', LIM); print('first model year', min(wf_log), wf_log[min(wf_log)])
for k, r in RES.items():
    d, l = r['databento'], r['lockbox2010']
    print(f"{r['name'][:34]:34s} | {d['cagr_pct']:5.1f} {d['sortino']:4.2f} {d['worst_drop_pct']:6.1f} {d['boot']:4.1f} | {l['cagr_pct']:5.1f} {l['sortino']:4.2f} {l['worst_drop_pct']:6.1f} {l['boot']:4.1f} | strict {r['strict_both']} growth {r['growth_both']} | 1.25x: {d['lev125']['cagr_pct']:5.1f} {d['lev125']['worst_drop_pct']:6.1f} {d['lev125']['boot21']:4.1f} / {l['lev125']['cagr_pct']:5.1f} {l['lev125']['worst_drop_pct']:6.1f} {l['lev125']['boot21']:4.1f} ok {r['lev125_both']}")
for k, v in diag.items(): print(' ', k, v)
