"""Batch 29 addendum 2: jitter test of G3 and skip-only (three pure-noise facts added to the 24).
Rules: addendum 2 in analysis/BATCH29_PREREG.md (committed before this file ran)."""
import os
A = os.path.dirname(os.path.abspath(__file__)); s29 = open(f'{A}/batch29.py').read(); BAR = '# ---------------------------------------------------------------- '
exec(s29.split(BAR + 'U1')[0])
# --- fast G3 pipeline (same as batch29b)
RID = [r['id'] for r in rows]; MON = np.array([r['date'][:7] for r in rows]); YV = np.array([FR[i][0] for i in RID]); STOP = np.array([FR[i][1] for i in RID])
F24 = np.array([r['f'] for r in rows], float); MONTHS = sorted(set(MON)); CUT = [(int(np.searchsorted(MON, m, 'left')), int(np.searchsorted(MON, m, 'right'))) for m in MONTHS]
def ridge(Xt, y):
    mu, sd = Xt.mean(0), Xt.std(0); sd[sd == 0] = 1; S = np.c_[np.ones(len(Xt)), (Xt - mu) / sd]; pen = np.eye(Xt.shape[1] + 1) * 100.0; pen[0, 0] = 0
    return mu, sd, np.linalg.solve(S.T @ S + pen, S.T @ y), S
def g3fast(X):
    PRv = np.full(len(rows), np.nan)
    for a, b in CUT:
        if a < 500 or b == a: continue
        mu, sd, bt, _ = ridge(X[:a], YV[:a]); PRv[a:b] = np.c_[np.ones(b - a), (X[a:b] - mu) / sd] @ bt
    G = {}; hist = []
    for k in range(len(rows)):
        p = PRv[k]
        if np.isnan(p): continue
        a_ = len(hist) >= 100 and p < np.quantile(hist[-252:], 1 / 3); b_ = p - 1.25 / STOP[k] <= 0
        G[RID[k]] = 0.0 if (a_ or b_) else 1.0; hist.append(p)
    return G
# --- fast skip-only (batch 14's W1m: net-R label, bottom third of the training predictions is skipped)
SID = [r['id'] for r in NQ]; SMON = np.array([r['date'][:7] for r in NQ]); SY = np.array([r['y'] for r in NQ]); SF = np.array([r['f'] for r in NQ], float)
SMONTHS = sorted(set(SMON)); SCUT = [(int(np.searchsorted(SMON, m, 'left')), int(np.searchsorted(SMON, m, 'right'))) for m in SMONTHS]
def sofast(X):
    G = {}
    for a, b in SCUT:
        if a < 500 or b == a: continue
        mu, sd, bt, S = ridge(X[:a], SY[:a]); lo = np.quantile(S @ bt, 1 / 3); p = np.c_[np.ones(b - a), (X[a:b] - mu) / sd] @ bt
        for k in range(a, b): G[SID[k]] = 0.0 if p[k - a] < lo else 1.0
    return G
assert g3fast(F24) == G3; so0 = sofast(SF); print('skip-only fast vs original: differing calls', sum(so0[i] != SO[i] for i in SO), 'of', len(SO), flush=True)
def stat(G):
    w = wfast(G); out = {}
    for e in ERAS: m = metrics(list(ret2(e, w[e]))); out[e] = (m['cagr_pct'], m['sortino'], m['worst_drop_pct'])
    return out
PK = {e: (BASE[e]['cagr_pct'], BASE[e]['sortino'], BASE[e]['worst_drop_pct']) for e in ERAS}
isq_g = np.array([TR[i]['strat'] == 'quantlab' for i in RID]); isq_s = np.array([TR[i]['strat'] == 'quantlab' for i in SID])
def jitter(fn, X, isq, ql_only, n=300):
    runs = []
    for _ in range(n):
        Z = rng.standard_normal((len(X), 3))
        if ql_only: Z[~isq] = 0.0
        runs.append(stat(fn(np.c_[X, Z])))
    out = {}
    for e in ERAS:
        a = np.array([r[e] for r in runs]); out[e] = {nm: dict(median=round(float(np.median(a[:, j])), 2), p5=round(float(np.quantile(a[:, j], .05)), 2), p95=round(float(np.quantile(a[:, j], .95)), 2)) for j, nm in enumerate(('return_pct', 'sortino', 'worst_drop_pct'))}
    out['share_beating_package_return_both_eras'] = round(float(np.mean([all(r[e][0] > PK[e][0] for e in ERAS) for r in runs])), 3)
    out['share_beating_package_sortino_both_eras'] = round(float(np.mean([all(r[e][1] > PK[e][1] for e in ERAS) for r in runs])), 3)
    out['share_worst_drop_no_deeper_than_package_both_eras'] = round(float(np.mean([all(r[e][2] >= PK[e][2] for e in ERAS) for r in runs])), 3)
    return out
RES = collections.OrderedDict(package=PK, G3_headline=stat(G3), skip_only_headline=stat(SO))
for nm, fn, X, isq in (('G3', g3fast, F24, isq_g), ('skip_only', sofast, SF, isq_s)):
    for lab, ql in (('all_trades', False), ('quantlab_only', True)):
        RES[f'{nm}_{lab}'] = jitter(fn, X, isq, ql); print(nm, lab, json.dumps(RES[f'{nm}_{lab}']), flush=True)
g, s = RES['G3_all_trades'], RES['skip_only_all_trades']
RES['skip_only_beats_G3_on_jitter_medians'] = bool(all(s[e]['return_pct']['median'] > g[e]['return_pct']['median'] and s[e]['sortino']['median'] > g[e]['sortino']['median'] for e in ERAS))
RES['G3_risk_improvement_robust'] = bool(g['share_beating_package_sortino_both_eras'] >= 0.8)
json.dump(RES, open(f'{A}/batch29c.json', 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
print('package', PK); print('G3 headline', RES['G3_headline'], 'skip-only headline', RES['skip_only_headline'])
print('skip-only beats G3 on jitter medians:', RES['skip_only_beats_G3_on_jitter_medians'], '| G3 risk improvement robust:', RES['G3_risk_improvement_robust'])
