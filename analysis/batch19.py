"""Batch 19 (14 Nov 2026). Rules and marks: analysis/BATCH19_PREREG.md (committed before this file ran)."""
import os, json
A = os.path.dirname(os.path.abspath(__file__))
exec(open(f'{A}/batch14.py').read().split('# ---- Part A')[0])
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingRegressor
STRAT = {}
for e in ERAS:
    for t in E[e]['tr']: STRAT[t['id']] = t['strat']
rows = sorted([r for r in NQ if r['f'] is not None], key=lambda r: r['date'])
def cuts(p): return np.quantile(p, [1 / 3, 2 / 3])
def bucket(p, lo, hi): return 0.5 if p < lo else (1.5 if p > hi else 1.0)
def std(X): mu, sd = X.mean(0), X.std(0); sd[sd == 0] = 1; return mu, sd
def ridge(X, y, lam=100.0):
    mu, sd = std(X); S = np.c_[np.ones(len(X)), (X - mu) / sd]; pen = np.eye(X.shape[1] + 1) * lam; pen[0, 0] = 0
    b = np.linalg.solve(S.T @ S + pen, S.T @ y); return lambda Z: np.c_[np.ones(len(Z)), (Z - mu) / sd] @ b
def rank_in(train_pred):
    srt = np.sort(train_pred); return lambda p: np.searchsorted(srt, p) / len(srt)
def run(model):
    W = {}
    for P_ in sorted({r['date'][:7] for r in rows}):
        trn = [r for r in rows if r['date'][:7] < P_]; tst = [r for r in rows if r['date'][:7] == P_]
        if len(trn) < 500 or not tst: continue
        X = np.array([r['f'] for r in trn]); y = np.array([r['y'] for r in trn]); Xt = np.array([r['f'] for r in tst])
        if model == 'M0' or model == 'M3':
            f = ridge(X, np.clip(y, -1, 3) if model == 'M3' else y); ptr, pts = f(X), f(Xt)
            lo, hi = cuts(ptr)
            for r, p in zip(tst, pts): W[r['id']] = bucket(p, lo, hi)
        elif model == 'M1':
            f0 = ridge(X, y); lo0, hi0 = cuts(f0(X))
            for s_ in ('quantlab', 'noiseband', 'atrband'):
                ix = [i for i, r in enumerate(trn) if STRAT[r['id']] == s_]; tx = [r for r in tst if STRAT[r['id']] == s_]
                if not tx: continue
                if len(ix) >= 300:
                    f = ridge(X[ix], y[ix]); lo, hi = cuts(f(X[ix])); pts = f(np.array([r['f'] for r in tx]))
                else: lo, hi = lo0, hi0; pts = f0(np.array([r['f'] for r in tx]))
                for r, p in zip(tx, pts): W[r['id']] = bucket(p, lo, hi)
        elif model == 'M2':
            mu, sd = std(X); m = LogisticRegression(C=0.01, max_iter=2000).fit((X - mu) / sd, (y > 0).astype(int))
            ptr = m.predict_proba((X - mu) / sd)[:, 1]; pts = m.predict_proba((Xt - mu) / sd)[:, 1]; lo, hi = cuts(ptr)
            for r, p in zip(tst, pts): W[r['id']] = bucket(p, lo, hi)
        elif model == 'M4':
            f = ridge(X, y); g = HistGradientBoostingRegressor(max_depth=3, max_iter=200, learning_rate=0.03, min_samples_leaf=100, random_state=0).fit(X, y)
            a_tr, b_tr = f(X), g.predict(X); ra, rb = rank_in(a_tr), rank_in(b_tr)
            ptr = (ra(a_tr) + rb(b_tr)) / 2; pts = (ra(f(Xt)) + rb(g.predict(Xt))) / 2; lo, hi = cuts(ptr)
            for r, p in zip(tst, pts): W[r['id']] = bucket(p, lo, hi)
    return W
MODELS = {m: run(m) for m in ('M0', 'M1', 'M2', 'M3', 'M4')}
PER = (('2013-17', '2013', '2018'), ('2018-20', '2018', '2021'), ('2021-26', '2021', '2027'))
def gap(W):
    out = {}
    for lab, a, b in PER:
        top = [r['y'] for r in rows if a <= r['date'] < b and W.get(r['id']) == 1.5]; bot = [r['y'] for r in rows if a <= r['date'] < b and W.get(r['id']) == 0.5]
        out[lab] = dict(top=round(np.mean(top), 3), bottom=round(np.mean(bot), 3), gap=round(np.mean(top) - np.mean(bot), 3), n_top=len(top), n_bot=len(bot))
    return out
GAPS = {m: gap(W) for m, W in MODELS.items()}
beats = {m: all(GAPS[m][lab]['gap'] > GAPS['M0'][lab]['gap'] for lab, _, _ in PER) for m in ('M1', 'M2', 'M3', 'M4')}
def series(e, mult, rw=0.5, cx=1.0):
    z = E[e]['z']; risk = z['risk']; R = collections.defaultdict(float)
    for t in E[e]['tr']:
        w = (mult.get(t['id'], 1.0) if (mult is not None and mom(t) and t['sym'] == 'NQ') else 1.0)
        R[t['date']] += w * t.get('w', 1.0) * (t['gross'] - cx * t['cost'])
    return [E[e]['core'][d] + rw * risk * R.get(d, 0.0) + z['tb'][d] for d in E[e]['days']]
SP = lambda W: {i: (0.0 if m == 0.5 else m) for i, m in W.items()}
SO = lambda W: {i: (0.0 if m == 0.5 else 1.0) for i, m in W.items()}
def avgsize(e, mult):
    tr = [t for t in E[e]['tr'] if mom(t) and t['sym'] == 'NQ' and t['date'] in E[e]['ds']]; return round(sum(mult.get(t['id'], 1.0) for t in tr) / len(tr), 3)
pkg = {}
for m, W in MODELS.items():
    pkg[m] = {e: dict(metrics(series(e, SP(W))), avg_size=avgsize(e, SP(W))) for e in ERAS}
cand = [m for m in ('M1', 'M2', 'M3', 'M4') if beats[m] and all(pkg[m][e]['cagr_pct'] > pkg['M0'][e]['cagr_pct'] and pkg[m][e]['sortino'] > pkg['M0'][e]['sortino'] and pkg[m][e]['avg_size'] <= pkg['M0'][e]['avg_size'] for e in ERAS)]
chosen = max(cand, key=lambda m: np.mean([GAPS[m][l]['gap'] for l, _, _ in PER])) if cand else 'M0'
# ---- Part B: double costs, judged by the growth mark against today's package at normal costs
IDX = {e: [E[e]['z']['ret'][d] for d in E[e]['days']] for e in ERAS}; LIM = {e: dict(drop=metrics(IDX[e])['worst_drop_pct'], boot=boot(IDX[e])) for e in ERAS}
B0 = {e: dict(metrics(series(e, None)), boot=boot(series(e, None))) for e in ERAS}
def growth(name, mult, cx):
    out = {'name': name}
    for e in ERAS:
        x = series(e, mult, 0.5, cx); h = dict(metrics(x), boot=boot(x)); b = B0[e]
        h['growth'] = bool(h['cagr_pct'] > b['cagr_pct'] and h['sortino'] > b['sortino'] and h['worst_drop_pct'] >= b['worst_drop_pct'] - 5 and h['worst_drop_pct'] >= LIM[e]['drop'] and h['boot'] <= LIM[e]['boot']); out[e] = h
    out['growth_both'] = out['databento']['growth'] and out['lockbox2010']['growth']; return out
W0 = MODELS['M0']; PB = collections.OrderedDict()
PB['package, double costs'] = growth('package today, double costs', None, 2.0)
PB['skip-only, double costs'] = growth('skip-only, double costs', SO(W0), 2.0)
PB['skip-and-press, double costs'] = growth('skip-and-press, double costs', SP(W0), 2.0)
if chosen != 'M0':
    PB['skip-only (chosen), double costs'] = growth(f'skip-only ({chosen}), double costs', SO(MODELS[chosen]), 2.0)
    PB['skip-and-press (chosen), double costs'] = growth(f'skip-and-press ({chosen}), double costs', SP(MODELS[chosen]), 2.0)
sp_ok = PB['skip-and-press, double costs']['growth_both']; so_ok = PB['skip-only, double costs']['growth_both']
main = 'skip-and-press' if sp_ok else ('skip-only' if so_ok else 'neither meets the growth mark at double costs')
json.dump(dict(skill_gaps=GAPS, beats_M0_all_three=beats, package_skip_and_press=pkg, chosen_model=chosen, double_costs=PB, limits=LIM, baseline_normal_costs=B0, main_book_by_rule=main), open(f'{A}/batch19.json', 'w'), indent=1)
for m in GAPS: print(m, {l: (v['top'], v['bottom'], v['gap']) for l, v in GAPS[m].items()}, 'beats M0' if beats.get(m) else '')
for m in pkg: print(m, {e: (v['cagr_pct'], v['sortino'], v['worst_drop_pct'], v['avg_size']) for e, v in pkg[m].items()})
print('chosen', chosen)
for k, r in PB.items():
    d, l = r['databento'], r['lockbox2010']; print(f"{k:38s} | {d['cagr_pct']:5.1f} {d['sortino']:4.2f} {d['worst_drop_pct']:6.1f} {d['boot']:5.1f} | {l['cagr_pct']:5.1f} {l['sortino']:4.2f} {l['worst_drop_pct']:6.1f} {l['boot']:5.1f} | growth {r['growth_both']}")
print('limits', LIM, '\nMAIN BOOK BY RULE:', main)
