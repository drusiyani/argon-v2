"""Batch 9 stage 2 (H5): learned day-quality sizing. Each era is sized by a ridge model trained ONLY on the other era.
Rules and pass mark: analysis/BATCH9_PREREG.md. Reads analysis/batch9_days_{era}.json written by batch9.py."""
import os, json, math, random
import numpy as np
A = os.path.dirname(os.path.abspath(__file__)); ERAS = ('databento', 'lockbox2010')
DATA = {e: json.load(open(f'{A}/batch9_days_{e}.json')) for e in ERAS}
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
            res[k].append(dd)
    return {k: round(100 * sum(b < -.35 for b in v) / draws, 1) for k, v in res.items()}
def fit(e):
    rows = [r for r in DATA[e]['rows'] if r['f']]; X = np.array([r['f'] for r in rows]); y = np.array([r['R'] for r in rows])
    mu, sd = X.mean(0), X.std(0); Z = (X - mu) / sd; Z1 = np.c_[np.ones(len(Z)), Z]; pen = np.eye(Z1.shape[1]); pen[0, 0] = 0
    w = np.linalg.solve(Z1.T @ Z1 + 1.0 * pen, Z1.T @ y); pred = Z1 @ w
    return dict(mu=mu, sd=sd, w=w, cuts=np.quantile(pred, [1 / 3, 2 / 3]))
def apply(model, e):
    risk = DATA[e]['risk']; base, sized, mult = [], [], []
    for r in DATA[e]['rows']:
        m = 1.0
        if r['f']:
            p = float(np.r_[1.0, (np.array(r['f']) - model['mu']) / model['sd']] @ model['w'])
            m = 0.5 if p < model['cuts'][0] else (1.5 if p > model['cuts'][1] else 1.0)
        base.append(r['core'] + 0.5 * risk * r['R'] + r['tb']); sized.append(r['core'] + 0.5 * risk * m * r['R'] + r['tb']); mult.append(m)
    return base, sized, mult
M = {e: fit(e) for e in ERAS}; out = {}
NAMES = ['VXN/median', 'VXN 5d change', '|gap|/ATR', 'prev |o-c|/ATR', '20d return', 'rules R prev 5d']
for e in ERAS:
    other = [x for x in ERAS if x != e][0]
    for label, model in (('out-of-era model (COUNTS)', M[other]), ('same-era model (in-sample, does not count)', M[e])):
        b, s, mult = apply(model, e); hb, hs = metrics(b), metrics(s); bt = boot({'b': b, 's': s})
        ok = hs['cagr_pct'] > hb['cagr_pct'] and hs['sortino'] > hb['sortino'] and hs['worst_drop_pct'] >= hb['worst_drop_pct'] - 1 and bt['s'] <= bt['b'] + 1
        rs = [(m, r['R']) for m, r in zip(mult, DATA[e]['rows'])]
        byb = {k: round(sum(R for m, R in rs if m == k) / max(1, sum(1 for m, _ in rs if m == k)), 3) for k in (0.5, 1.0, 1.5)}
        out.setdefault(e, {})[label] = dict(verdict='PASS' if ok else 'FAIL', baseline=hb, sized=hs, boot_drop35=bt, avg_rule_R_per_day_by_size=byb,
                                            days_by_size={k: sum(1 for m in mult if m == k) for k in (0.5, 1.0, 1.5)})
    out[e]['weights_of_model_trained_here'] = dict(zip(['intercept'] + NAMES, [round(float(x), 4) for x in M[e]['w']]))
json.dump(out, open(f'{A}/batch9_ml.json', 'w'), indent=1); print(json.dumps(out, indent=1))
