"""Batch 14 (14 Nov 2026). Rules and pass marks: analysis/BATCH14_PREREG.md (committed before this file ran).
Step 2: reads analysis/_cache/batch14_{era}.pkl written by batch14_dump.py."""
import os, json, math, random, pickle, collections, statistics, datetime as dt
import numpy as np
A = os.path.dirname(os.path.abspath(__file__)); ERAS = ('databento', 'lockbox2010')
Z = {e: pickle.load(open(f'{A}/_cache/batch14_{e}.pkl', 'rb')) for e in ERAS}
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
def mom(t): return t['strat'] != 'expiry'
def rows24(tr, D, atr, on, dl, ds, w):
    """The 24 batch-13 features for every momentum trade (identical code path for Nasdaq and S&P trades)."""
    pos = {d: k for k, d in enumerate(dl)}; YR = collections.defaultdict(float); YN = collections.Counter(); byday = collections.defaultdict(list); out = []
    for t in tr:
        if mom(t): YR[t['date']] += t['gross'] - t['cost']; YN[t['date']] += 1; byday[t['date']].append(t)
    for d, L in byday.items():
        L.sort(key=lambda t: t['entry_min']); k = pos.get(d, 0)
        if k == 0 or d not in ds or d not in atr or dl[k - 1] not in atr or k < 22: continue
        p = dl[k - 1]; o, h, l, cl = D[d]; po, ph, pl, pc = D[p]; a, ap = atr[d], atr[p]; onh, onl, _ = on.get(d, (o, o, o)); cloc = (pc - pl) / (ph - pl) if ph > pl else .5
        ql = [x for x in L if x['strat'] == 'quantlab']; qs = (1 if ql[0]['side'] in (1, 'long') else -1) if ql else 0
        for j, t in enumerate(L):
            s = 1 if t['side'] in (1, 'long') else -1; g = (o - pc) * s; y = (pc - po) * s
            sofar = sum(x['gross'] - x['cost'] for x in L[:j] if x['exit_min'] <= t['entry_min'])
            same = sum(1 for x in L[:j] if x['exit_min'] > t['entry_min'] and (1 if x['side'] in (1, 'long') else -1) == s)
            f = [sg(g), abs(o - pc) / a, clip(g / a, 3), clip(y / ap, 3), clip(s * (pc - D[dl[k - 2]][3]) / ap, 3), clip(s * (pc - D[dl[k - 6]][3]) / a / math.sqrt(5), 3),
                 clip(s * (pc - D[dl[k - 21]][3]) / a / math.sqrt(20), 3), (1 if ((o > ph and s == 1) or (o < pl and s == -1)) else (-1 if (o > ph or o < pl) else 0)),
                 s * (2 * cloc - 1), (ph - pl) / ap, clip(YR[p], 5), 1.0 if YN[p] == 0 else 0.0, w.get(d, 1.0), s, 1.0 if t['strat'] == 'quantlab' else 0.0,
                 1.0 if t['strat'] == 'noiseband' else 0.0, (t['entry_min'] - 570) / 390, t['risk_pts'] / a, min(same, 2), min(j + 1, 3),
                 0 if (t['strat'] == 'quantlab' or not qs) else qs * s, 1.0 if dt.date.fromisoformat(d).weekday() == 0 else 0.0,
                 s * (2 * (o - onl) / (onh - onl) - 1) if onh > onl else 0.0, clip(sofar, 3)]
            out.append(dict(id=t['id'], date=d, y=t['gross'] - t['cost'], f=f))
    return out
E = {}; NQ = []; ES = []
for e in ERAS:
    z = Z[e]; tr = [dict(t, id=(e, i)) for i, t in enumerate(z['trades'])]; ds = set(z['days'])
    r = rows24([t for t in tr if t['sym'] == 'NQ'], z['D'], z['atr'], z['on'], z['dl'], ds, z['w'])
    for x in r: x['x'] = z['ext'].get(x['id'][1])
    NQ += r
    es = z['es']; etr = [dict(t, id=('ES' + e, i)) for i, t in enumerate(es['trades'])]
    ES += rows24(etr, es['D'], es['atr'], es['on'], es['dl'], set(es['dl']), z['w'])
    E[e] = dict(z=z, tr=tr, etr={t['id']: t for t in etr}, days=z['days'], ds=ds, core={d: z['w'][d] * z['ret'][d] + z['fomc'].get(d, 0.0) for d in z['dl'][1:]})
NQ.sort(key=lambda r: r['date']); ES.sort(key=lambda r: r['date'])
def fit(X, y, lam=100.0):
    mu, sd = X.mean(0), X.std(0); sd[sd == 0] = 1; S = np.c_[np.ones(len(X)), (X - mu) / sd]; pen = np.eye(X.shape[1] + 1) * lam; pen[0, 0] = 0
    b = np.linalg.solve(S.T @ S + pen, S.T @ y); lo, hi = np.quantile(S @ b, [1 / 3, 2 / 3]); return dict(mu=mu, sd=sd, b=b, lo=lo, hi=hi)
def size(m, f): p = float(np.r_[1.0, (np.array(f) - m['mu']) / m['sd']] @ m['b']); return 0.5 if p < m['lo'] else (1.5 if p > m['hi'] else 1.0)
def walk(rows, feat, klen):
    """klen 4 = refit each year, 7 = refit each month; a period's model sees only rows dated before that period."""
    rows = [r for r in rows if feat(r) is not None]; W = {}; models = {}
    for P_ in sorted({r['date'][:klen] for r in rows}):
        trn = [r for r in rows if r['date'][:klen] < P_]
        if len(trn) < 500: continue
        m = fit(np.array([feat(r) for r in trn]), np.array([r['y'] for r in trn])); models[P_] = m
        for r in rows:
            if r['date'][:klen] == P_: W[r['id']] = size(m, feat(r))
    return W, models
f24 = lambda r: r['f']; f52 = lambda r: (r['f'] + r['x']) if r.get('x') else None
W1, M1y = walk(NQ, f24, 4); W1m, _ = walk(NQ, f24, 7); W3, M3 = walk(NQ, f52, 7)
# ---- Part A: the Nasdaq-trained yearly model sizes S&P trades
WES = {r['id']: size(M1y[r['date'][:4]], r['f']) for r in ES if r['date'][:4] in M1y}
def bucket(rows, W, a, b):
    out = {}
    for m in (0.5, 1.0, 1.5):
        v = [r['y'] for r in rows if a <= r['date'] < b and W.get(r['id']) == m]; out[f'x{m}'] = dict(trades=len(v), avg_R=round(sum(v) / len(v), 3) if v else None)
    return out
PER = (('2013-17', '2013', '2018'), ('2018-20', '2018', '2021'), ('2021-26', '2021', '2027'))
partA = {lab: bucket(ES, WES, a, b) for lab, a, b in PER}
replicates = all(partA[lab]['x1.5']['avg_R'] > partA[lab]['x0.5']['avg_R'] for lab, _, _ in PER)
top_pos = all(bucket(ES, WES, a, b)['x1.5']['avg_R'] > 0 for a, b in (('2013', '2021'), ('2021', '2027')))
partA_summary = dict(by_period=partA, top_third_2013_20=bucket(ES, WES, '2013', '2021')['x1.5'], top_third_2021_26=bucket(ES, WES, '2021', '2027')['x1.5'], replicates=bool(replicates), part_B_condition_met=bool(replicates and top_pos))
# ---- series and scoring
def series(e, W=None, k=1.0, es=False):
    z = E[e]['z']; risk = z['risk']; R = collections.defaultdict(float)
    for t in E[e]['tr']: R[t['date']] += (W.get(t['id'], 1.0) if (W is not None and mom(t) and t['sym'] == 'NQ') else 1.0) * net(t)
    if es:
        for i_, t in E[e]['etr'].items():
            if WES.get(i_) == 1.5: R[t['date']] += t['gross'] - t['cost']
    return [k * (E[e]['core'][d] + 0.5 * risk * R.get(d, 0.0)) + z['tb'][d] for d in E[e]['days']]
IDX = {e: [E[e]['z']['ret'][d] for d in E[e]['days']] for e in ERAS}; LIM = {e: dict(drop=metrics(IDX[e])['worst_drop_pct'], boot=boot(IDX[e])) for e in ERAS}
B0 = {e: dict(metrics(series(e)), boot=boot(series(e))) for e in ERAS}
def score(name, **kw):
    out = {'name': name}
    for e in ERAS:
        x = series(e, **kw); h = dict(metrics(x), boot=boot(x)); b = B0[e]; better = h['cagr_pct'] > b['cagr_pct'] and h['sortino'] > b['sortino']
        h['strict'] = bool(better and h['worst_drop_pct'] >= b['worst_drop_pct'] - 1 and h['boot'] <= b['boot'] + 1)
        h['growth'] = bool(better and h['worst_drop_pct'] >= b['worst_drop_pct'] - 5 and h['worst_drop_pct'] >= LIM[e]['drop'] and h['boot'] <= LIM[e]['boot'])
        x125 = series(e, k=1.25, **kw); h['lev125'] = dict(metrics(x125), boot21=boot(x125, B=21)); h['lev125']['ok'] = bool(h['lev125']['worst_drop_pct'] > -35 and h['lev125']['boot21'] < 20); out[e] = h
    out['strict_both'] = out['databento']['strict'] and out['lockbox2010']['strict']; out['growth_both'] = out['databento']['growth'] and out['lockbox2010']['growth']
    out['lev125_both'] = out['databento']['lev125']['ok'] and out['lockbox2010']['lev125']['ok']; return out
RES = collections.OrderedDict(); RES['baseline'] = score('package baseline')
RES['W1'] = score('W1 yearly, 24 features (batch 13)', W=W1); RES['W1m'] = score('W1m monthly, 24 features', W=W1m); RES['W3'] = score('W3 monthly, 52 features', W=W3)
def beats(a, b): return RES[a]['growth_both'] and all(RES[a][e]['cagr_pct'] > RES[b][e]['cagr_pct'] and RES[a][e]['sortino'] > RES[b][e]['sortino'] for e in ERAS)
chosen = 'W3' if beats('W3', 'W1') else ('W1m' if beats('W1m', 'W1') else 'W1'); WC = {'W1': W1, 'W1m': W1m, 'W3': W3}[chosen]
if partA_summary['part_B_condition_met']:
    RES['B'] = score('package + S&P top-third trades', es=True)
    RES['D'] = score(f'candidate: {chosen} sizing + S&P top-third trades', W=WC, es=True) if RES['B']['growth_both'] else score(f'candidate: {chosen} sizing', W=WC)
else: RES['D'] = score(f'candidate: {chosen} sizing', W=WC)
# ---- diagnostics
diag = {nm: {lab: bucket(NQ, W_, a, b) for lab, a, b in PER} for nm, W_ in (('W1', W1), ('W1m', W1m), ('W3', W3))}
NAMES = ['gap dir', '|gap|', 'gap signed', 'yesterday o-c', 'yesterday c-c', '5d', '20d', 'open outside range', 'yesterday close loc', 'yesterday range', 'yesterday rules R', 'no trades yesterday',
         'VXN weight', 'side', 'is QuantLab', 'is noise band', 'time of day', 'stop size', 'same-dir open', 'trade number', 'vs QuantLab', 'Monday', 'open in overnight range', 'rules R so far today',
         'dist from open', 'range position', 'dist from VWAP', 'opening range', 'movement so far', 'volume so far', 'S&P move', 'NQ minus S&P', 'pre-mkt volume', '08:30 reaction', 'overnight range', 'overnight dir',
         'expiry week', 'Fed tomorrow', 'Fed yesterday', 'month end', 'month start', 'Tue', 'Wed', 'Thu', 'Fri', '10y 5d', '10y-2y', 'dollar 5d', 'policy uncertainty', 'oil 5d', 'VIX/VIX3M', 'VXN 5d']
last = M3[max(M3)]; coef = sorted(zip(NAMES, [round(float(v), 4) for v in last['b'][1:]]), key=lambda kv: -abs(kv[1]))
luck = None
if chosen != 'W1':
    by = collections.defaultdict(list)
    for r in NQ:
        if r['id'] in WC: by[r['date'][:4]].append(r['id'])
    rng = random.Random(7); sims = {e: [] for e in ERAS}
    for _ in range(300):
        sh = {}
        for y, ids in by.items(): v = [WC[i] for i in ids]; rng.shuffle(v); sh.update(zip(ids, v))
        for e in ERAS: sims[e].append(metrics(series(e, W=sh))['cagr_pct'])
    luck = {e: dict(model=RES[chosen][e]['cagr_pct'], shuffled_mean=round(sum(sims[e]) / 300, 1), shuffles_beating_model=sum(s >= RES[chosen][e]['cagr_pct'] for s in sims[e])) for e in ERAS}
json.dump(dict(limits_index_alone=LIM, baseline=B0, part_A=partA_summary, results=RES, chosen_model=chosen, nasdaq_buckets=diag, W3_latest_weights=coef, luck_check=luck,
               rows=dict(nasdaq=len(NQ), nasdaq_with_new_features=sum(1 for r in NQ if r.get('x')), sp=len(ES))), open(f'{A}/batch14.json', 'w'), indent=1)
print('rows', len(NQ), sum(1 for r in NQ if r.get('x')), len(ES)); print('PART A', json.dumps(partA_summary)); print('chosen', chosen, 'luck', luck)
for k, r in RES.items():
    d, l = r['databento'], r['lockbox2010']
    print(f"{r['name'][:44]:44s} | {d['cagr_pct']:5.1f} {d['sharpe']:4.2f} {d['sortino']:4.2f} {d['worst_drop_pct']:6.1f} {d['boot']:4.1f} | {l['cagr_pct']:5.1f} {l['sharpe']:4.2f} {l['sortino']:4.2f} {l['worst_drop_pct']:6.1f} {l['boot']:4.1f} | strict {r['strict_both']} growth {r['growth_both']} | 1.25x {d['lev125']['cagr_pct']:5.1f} {d['lev125']['worst_drop_pct']:6.1f} {d['lev125']['boot21']:4.1f} / {l['lev125']['cagr_pct']:5.1f} {l['lev125']['worst_drop_pct']:6.1f} {l['lev125']['boot21']:4.1f} ok {r['lev125_both']}")
for nm in diag: print(nm, {lab: (v['x0.5']['avg_R'], v['x1.0']['avg_R'], v['x1.5']['avg_R']) for lab, v in diag[nm].items()})
print('W3 top weights', coef[:16])
