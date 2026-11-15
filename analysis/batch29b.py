"""Batch 29 addendum checks for U4 and the U4b trial. Rules: the addendum in analysis/BATCH29_PREREG.md
(committed before this file ran)."""
import os
A = os.path.dirname(os.path.abspath(__file__)); s29 = open(f'{A}/batch29.py').read(); BAR = '# ---------------------------------------------------------------- '
exec(s29.split(BAR + 'U1')[0]); exec(s29.split(BAR + 'U4: shape of the signal candle')[1].split(BAR + 'U5')[0].split("G_u4, _ = pipeline")[0])
RID = [r['id'] for r in rows]; MON = np.array([r['date'][:7] for r in rows]); YRS = np.array([r['date'][:4] for r in rows]); YV = np.array([FR[i][0] for i in RID]); STOP = np.array([FR[i][1] for i in RID])
F24 = np.array([r['f'] for r in rows], float); MONTHS = sorted(set(MON)); CUT = [(int(np.searchsorted(MON, m, 'left')), int(np.searchsorted(MON, m, 'right'))) for m in MONTHS]
def fastpipe(X, betas=None):
    PRv = np.full(len(rows), np.nan)
    for (a, b), m in zip(CUT, MONTHS):
        if a < 500 or b == a: continue
        Xt = X[:a]; mu, sd = Xt.mean(0), Xt.std(0); sd[sd == 0] = 1; S = np.c_[np.ones(a), (Xt - mu) / sd]; pen = np.eye(X.shape[1] + 1) * 100.0; pen[0, 0] = 0
        bt = np.linalg.solve(S.T @ S + pen, S.T @ YV[:a]); PRv[a:b] = np.c_[np.ones(b - a), (X[a:b] - mu) / sd] @ bt
        if betas is not None: betas[m] = bt
    G = {}; hist = []
    for k in range(len(rows)):
        p = PRv[k]
        if np.isnan(p): continue
        a_ = len(hist) >= 100 and p < np.quantile(hist[-252:], 1 / 3); b_ = p - 1.25 / STOP[k] <= 0
        G[RID[k]] = 0.0 if (a_ or b_) else 1.0; hist.append(p)
    return G
Gf = fastpipe(F24); print('fast pipeline vs G3: differing calls', sum(Gf[i] != G3[i] for i in G3), flush=True)
SHQ = np.array([SH[i] for i in RID], float); BT = {}; G4 = fastpipe(np.c_[F24, SHQ], BT)
def stats(G, cx=1.0):
    w = wfast(G); out = {}
    for e in ERAS:
        q = Q[e]; nr = np.array([t.get('w', 1.0) * (t['gross'] - cx * t['cost']) for t in q['tr']]); out[e] = q['base'] + 0.5 * q['risk'] * np.bincount(q['day'], weights=w[e] * nr, minlength=q['nd'])
    return out
def mt(x): m = metrics(list(x)); return m
R3 = stats(G3); R4 = stats(G4); C3 = {e: cagr(R3[e]) for e in ERAS}; C4 = {e: cagr(R4[e]) for e in ERAS}; M3 = {e: mt(R3[e]) for e in ERAS}
print('U4 via fast pipeline', {e: round(C4[e], 2) for e in ERAS}, 'G3', {e: round(C3[e], 2) for e in ERAS}, flush=True)
def near_strict(R): return all(cagr(R[e]) > C3[e] and mt(R[e])['sortino'] > M3[e]['sortino'] and mt(R[e])['worst_drop_pct'] >= M3[e]['worst_drop_pct'] - 1 for e in ERAS)
def junk(SHP, mask, target, n=300):
    """Shuffle the shape rows among the masked trades within each year; count junk runs matching the target return in both eras."""
    yidx = [np.where(mask & (YRS == y))[0] for y in sorted(set(YRS))]; yidx = [ix for ix in yidx if len(ix) > 1]; hit = fp = 0; dist = {e: [] for e in ERAS}
    for _ in range(n):
        Z = SHP.copy()
        for ix in yidx: Z[ix] = SHP[rng.permutation(ix)]
        R = stats(fastpipe(np.c_[F24, Z])); hit += all(cagr(R[e]) >= target[e] for e in ERAS); fp += near_strict(R)
        for e in ERAS: dist[e].append(cagr(R[e]))
    return dict(runs=n, junk_matching_idea_both_eras=int(hit), junk_passing_strict_like_mark_vs_G3=int(fp),
                junk_return_median={e: round(float(np.median(dist[e])), 2) for e in ERAS}, junk_return_p95={e: round(float(np.quantile(dist[e], .95)), 2) for e in ERAS})
RES = collections.OrderedDict()
isq = np.array([TR[i]['strat'] == 'quantlab' for i in RID])
A_ = junk(SHQ, isq, C4); A_['pass'] = bool(A_['junk_matching_idea_both_eras'] / A_['runs'] < 0.05); print('Check A', A_, flush=True)
# Check B: double costs
B3 = stats(G3, 2.0); B4 = stats(G4, 2.0); B_ = {e: dict(G3=round(cagr(B3[e]), 1), U4=round(cagr(B4[e]), 1)) for e in ERAS}; B_['pass'] = bool(all(cagr(B4[e]) > cagr(B3[e]) for e in ERAS)); print('Check B', B_, flush=True)
# Check C: sub-periods
SUB = (('2010-13', '2010', '2014'), ('2014-17', '2014', '2018'), ('2018-20', '2018', '2021'), ('2021-25', '2021', '2026'), ('2026', '2026', '2027'))
def sub(R):
    out = {}
    for lab, a, b in SUB:
        e = 'lockbox2010' if a < '2021' else 'databento'; m = np.array([a <= d < b for d in E[e]['days']]); out[lab] = round(cagr(R[e][m]), 1)
    return out
C_ = dict(G3=sub(R3), U4=sub(R4)); C_['level_or_better'] = int(sum(C_['U4'][k] >= C_['G3'][k] - 0.1 for k in C_['G3'])); C_['pass'] = bool(C_['level_or_better'] >= 4); print('Check C', C_, flush=True)
# reported: changed calls, weight signs
def changed(G):
    out = {}
    for e in ERAS:
        ns = [TR[i]['gross'] - TR[i]['cost'] for i in G if i[0] == e and i in G3 and G3[i] == 1.0 and G[i] == 0.0]; nk = [TR[i]['gross'] - TR[i]['cost'] for i in G if i[0] == e and i in G3 and G3[i] == 0.0 and G[i] == 1.0]
        out[e] = dict(newly_skipped=len(ns), newly_skipped_avg_net_R=round(float(np.mean(ns)), 3) if ns else None, newly_kept=len(nk), newly_kept_avg_net_R=round(float(np.mean(nk)), 3) if nk else None)
    return out
names = ('close_location', 'last_minute_share', 'volume_tilt'); bm = np.array([BT[m][-3:] for m in sorted(BT)])
wsign = {n: dict(last=round(float(bm[-1, j]), 4), mean=round(float(bm[:, j].mean()), 4), share_of_months_positive=round(float((bm[:, j] > 0).mean()), 2)) for j, n in enumerate(names)}
ch4 = changed(G4); print('changed calls', ch4); print('weights', wsign, flush=True)
RES['U4_checks'] = dict(A_junk_facts=A_, B_double_costs=B_, C_sub_periods=C_, changed_calls=ch4, weights=wsign, adopt_candidate=bool(A_['pass'] and B_['pass'] and C_['pass']))

# ---------------------------------------------------------------- U4b: the same three facts for every rule (five 1-minute bars before entry)
def shape_all(i):
    t = TR[i]; em = t['entry_min']; B = [b for b in C29[i[0]]['m1'].get(t['date'], []) if em - 5 <= b[0] <= em - 1]
    if len(B) < 5: return [0.0, 0.0, 0.0]
    o, c_ = B[0][1], B[-1][4]; hi = max(b[2] for b in B); lo = min(b[3] for b in B); s = side(t)
    clv = s * (2 * (c_ - lo) / (hi - lo) - 1) if hi > lo else 0.0; sh = clip((c_ - B[-2][4]) / (c_ - o), 2) if c_ != o else 0.0
    v0, v1 = B[0][5] + B[1][5], B[3][5] + B[4][5]; lv = math.log(v1 / v0) if v0 > 0 and v1 > 0 else 0.0
    return [clv, sh, clip(lv, 3)]
SHA = np.array([shape_all(i) for i in RID], float); assert np.allclose(SHA[isq], SHQ[isq]), 'QuantLab rows should be identical in U4 and U4b'
G4b = fastpipe(np.c_[F24, SHA]); w = wfast(G4b); res = {e: full(ret2(e, w[e])) for e in ERAS}; R4b = stats(G4b); C4b = {e: cagr(R4b[e]) for e in ERAS}
okb = judge('U4b_shape_all_rules', res, luck(G4b)); r4 = {e: full(ret2(e, wfast(G4)[e])) for e in ERAS}
beats_u4 = bool(all(res[e]['cagr_pct'] > r4[e]['cagr_pct'] and res[e]['sortino'] > r4[e]['sortino'] for e in ERAS))
Ab = junk(SHA, np.ones(len(RID), bool), C4b); Ab['pass'] = bool(Ab['junk_matching_idea_both_eras'] / Ab['runs'] < 0.05); print('U4b junk twin', Ab, 'beats U4', beats_u4, flush=True)
OUT['U4b_shape_all_rules'].update(junk_facts=Ab, beats_U4_both_eras=beats_u4, sub_periods=sub(R4b), changed_calls=changed(G4b), adopt_candidate=bool(okb and Ab['pass'] and OUT['U4b_shape_all_rules']['luck_pass']))
RES['U4_result'] = r4; RES['U4b'] = OUT['U4b_shape_all_rules']; RES['G3'] = REF
json.dump(RES, open(f'{A}/batch29b.json', 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
print('U4 adopt candidate after checks:', RES['U4_checks']['adopt_candidate'], '| U4b adopt candidate:', RES['U4b']['adopt_candidate'])
