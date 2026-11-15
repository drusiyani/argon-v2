"""Batch 25 (15 Nov 2026). Rules and marks: analysis/BATCH25_PREREG.md (committed before this file ran).
Needs the batch 14 / 24 / 25 caches."""
import os, json, pickle
A = os.path.dirname(os.path.abspath(__file__))
src24 = open(f'{A}/batch24.py').read()
exec(src24.split('# ---- vectorised package returns per era')[0])          # rebuilds G3, PRED, rows, FR exactly as batch 24
vec = src24.split('# ---- vectorised package returns per era')[1].split('ELIG = {')[0]; exec(vec)   # Q, ret, cagr, full, wvec, strict
X25 = {e: pickle.load(open(f'{A}/_cache/batch25_{e}.pkl', 'rb'))['x'] for e in ERAS}
def x(i): return X25[i[0]].get(KEY[i])
# A-condition per row, exactly as G3
Acond = {}; hist = []
for r in rows:
    if r['id'] not in PRED: continue
    p = PRED[r['id']]; Acond[r['id']] = len(hist) >= 100 and p < np.quantile(hist[-252:], 1 / 3); hist.append(p)
def on_top(flagf): return {i: (0.0 if (m == 0.0 or flagf(i)) else 1.0) for i, m in G3.items()}
T1 = on_top(lambda i: bool(x(i) and x(i)['noise'] and x(i)['stop'] < x(i)['noise']))
T2 = on_top(lambda i: bool(x(i) and x(i)['T2_skip']))
T5 = on_top(lambda i: bool(x(i) and x(i)['er'] is not None and x(i)['er'] < 0.20))
T3 = {i: (0.0 if (Acond[i] or (PRED[i] - (x(i)['fric3'] if x(i) else 1.25 / FR[i][1]) <= 0)) else 1.0) for i in G3}
# T4 two-stage
E4 = {}
for P_ in sorted({r['date'][:7] for r in rows}):
    trn = [r for r in rows if r['date'][:7] < P_]; tst = [r for r in rows if r['date'][:7] == P_]
    if len(trn) < 500 or not tst: continue
    Xt = np.array([r['f'] for r in trn]); y = np.array([FR[r['id']][0] for r in trn]); mu, sd = Xt.mean(0), Xt.std(0); sd[sd == 0] = 1; Z_ = (Xt - mu) / sd
    def rfit(Zm, yv, lam):
        S = np.c_[np.ones(len(Zm)), Zm]; pen = np.eye(Zm.shape[1] + 1) * lam; pen[0, 0] = 0; return np.linalg.solve(S.T @ S + pen, S.T @ yv)
    b1 = rfit(Z_, (y > 0).astype(float), 100.0); win = y > 0
    if win.sum() < 200: continue
    b2 = rfit(Z_[win], np.log1p(y[win]), 200.0); loss = float(y[~win].mean())
    for r in tst:
        z = np.r_[1.0, (np.array(r['f']) - mu) / sd]; p = float(np.clip(z @ b1, 0.05, 0.95)); m_ = float(np.expm1(z @ b2)); E4[r['id']] = p * m_ + (1 - p) * loss
T4 = {}; h4 = []
for r in rows:
    if r['id'] not in E4: continue
    e_ = E4[r['id']]; a_ = len(h4) >= 100 and e_ < np.quantile(h4[-252:], 1 / 3); T4[r['id']] = 0.0 if (a_ or e_ - 1.25 / FR[r['id']][1] <= 0) else 1.0; h4.append(e_)
REF = {e: full(ret(e, wvec(e, G3))) for e in ERAS}; rng = np.random.default_rng(20261116); N = 5000; RES = collections.OrderedDict()
def extra_luck(M):
    grp = {e: [] for e in ERAS}
    for e in ERAS:
        tr = Q[e]['tr']; kept = np.array([G3.get(t['id'], 1.0) == 1.0 and t['id'] in G3 for t in tr]); ex = np.array([kept[i] and M.get(t['id'], 1.0) == 0.0 for i, t in enumerate(tr)])
        for y in sorted(set(Q[e]['yr'])):
            idx = np.where(kept & (Q[e]['yr'] == y))[0]; k = int(ex[idx].sum())
            if k: grp[e].append((idx, k))
    tgt = {e: cagr(ret(e, wvec(e, M))) for e in ERAS}; base_w = {e: wvec(e, G3) for e in ERAS}; hits = 0
    for _ in range(N):
        ok = True
        for e in ERAS:
            w = base_w[e].copy()
            for idx, k in grp[e]: w[rng.choice(idx, k, replace=False)] = 0.0
            ok &= cagr(ret(e, w)) >= tgt[e]
        hits += ok
    return int(hits)
def shuffle_luck(M):
    by = collections.defaultdict(list)
    for r in rows:
        if r['id'] in M: by[r['date'][:4]].append(r['id'])
    tgt = {e: cagr(ret(e, wvec(e, M))) for e in ERAS}; hits = 0
    for _ in range(N):
        sh = {}
        for y, L in by.items(): v = [M[i] for i in L]; rng.shuffle(v); sh.update(zip(L, v))
        hits += all(cagr(ret(e, wvec(e, sh))) >= tgt[e] for e in ERAS)
    return int(hits)
PER = (('2010-13', '2010', '2014'), ('2014-17', '2014', '2018'), ('2018-20', '2018', '2021'), ('2021-25', '2021', '2026'), ('2026', '2026', '2027'))
def removed_vs_kept(M):
    out = {}
    for lab, a, b in PER:
        rr = [r for r in rows if a <= r['date'] < b and r['id'] in M and r['id'] in G3]
        rem = [r['y'] for r in rr if G3[r['id']] == 1.0 and M[r['id']] == 0.0]; add = [r['y'] for r in rr if G3[r['id']] == 0.0 and M[r['id']] == 1.0]
        kept = [r['y'] for r in rr if M[r['id']] == 1.0]
        out[lab] = dict(newly_skipped=len(rem), newly_skipped_avg_R=round(float(np.mean(rem)), 3) if rem else None, newly_taken=len(add),
                        newly_taken_avg_R=round(float(np.mean(add)), 3) if add else None, kept_avg_R=round(float(np.mean(kept)), 3) if kept else None)
    return out
for nm, M, kind in (('T1 stop inside noise', T1, 'extra'), ('T2 remaining range', T2, 'extra'), ('T3 dynamic friction', T3, 'shuffle'), ('T4 two-stage model', T4, 'shuffle'), ('T5 path efficiency', T5, 'extra')):
    h = {e: full(ret(e, wvec(e, M))) for e in ERAS}; m1 = all(strict(h[e], REF[e]) for e in ERAS)
    luck = extra_luck(M) if kind == 'extra' else shuffle_luck(M)
    RES[nm] = dict(result=h, strict_vs_G3=bool(m1), luck_random_beating_both_eras=luck, luck_pass=bool(luck / N < 0.05), adopt_candidate=bool(m1 and luck / N < 0.05),
                   skip_share={e: round(1 - float(np.mean([M.get(t['id'], 1.0) for t in Q[e]['tr'] if t['id'] in M])), 3) for e in ERAS}, vs_G3=removed_vs_kept(M))
json.dump(dict(G3=REF, results=RES), open(f'{A}/batch25.json', 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
fmt = lambda h: f"{h['cagr_pct']:5.1f} {h['sortino']:4.2f} {h['worst_drop_pct']:6.1f} {h['boot']:5.1f}"
print('G3       ', ' | '.join(fmt(REF[e]) for e in ERAS))
for nm, r in RES.items():
    print(f"{nm:22s}", ' | '.join(fmt(r['result'][e]) for e in ERAS), '| strict', r['strict_vs_G3'], 'luck', r['luck_random_beating_both_eras'], 'skips', r['skip_share'], 'ADOPT' if r['adopt_candidate'] else '')
    print('    ', r['vs_G3'])
