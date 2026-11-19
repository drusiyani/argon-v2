"""Batch 31: Gemini T13. Rules: analysis/BATCH31_PREREG.md (committed before this file ran)."""
import os
A = os.path.dirname(os.path.abspath(__file__)); s29 = open(f'{A}/batch29.py').read(); BAR = '# ---------------------------------------------------------------- '
exec(s29.split(BAR + 'U1')[0]); OUT = collections.OrderedDict(G3=REF)
# ---- V1 pre-settlement overnight leg
def legs(e):
    z = E[e]['z']; D = z['D']; out = []
    for d in E[e]['days']:
        r = z['ret'][d]; o, h, l, c_ = D[d]; dy = c_ / o - 1; ng = 0.0 if r == 0.0 else (1 + r) / (1 + dy) - 1
        out.append((d, ng, z['w'][d], o))
    return out
LG = {e: legs(e) for e in ERAS}
isfri = lambda d: dt.date.fromisoformat(d).weekday() == 4
isexp = lambda d: isfri(d) and 15 <= int(d[8:]) <= 21
def v1ret(e, sel):
    x = np.array([(0.5 * w * ng - 0.5 * w * 1.25 / px) if d in sel else 0.0 for d, ng, w, px in LG[e]]); return ret2(e, WG3[e], base=Q[e]['base'] + x)
diag = {}
for e in ERAS:
    a = [ng for d, ng, w, px in LG[e] if isexp(d)]; b = [ng for d, ng, w, px in LG[e] if isfri(d) and not isexp(d)]
    diag[e] = dict(expiry_fridays=len(a), expiry_avg_night_bp=round(1e4 * float(np.mean(a)), 1), other_fridays=len(b), other_avg_night_bp=round(1e4 * float(np.mean(b)), 1))
SEL = {e: {d for d, *_ in LG[e] if isexp(d)} for e in ERAS}; R1 = {e: v1ret(e, SEL[e]) for e in ERAS}; res1 = {e: full(R1[e]) for e in ERAS}
tgt = {e: cagr(R1[e]) for e in ERAS}; pool = {e: collections.defaultdict(list) for e in ERAS}; cnt = {e: collections.Counter() for e in ERAS}
for e in ERAS:
    for d, *_ in LG[e]:
        if isfri(d) and not isexp(d): pool[e][d[:4]].append(d)
        if isexp(d): cnt[e][d[:4]] += 1
hits = 0
for _ in range(N):
    hits += all(cagr(v1ret(e, {x for y, k in cnt[e].items() for x in rng.choice(pool[e][y], size=min(k, len(pool[e][y])), replace=False)})) >= tgt[e] for e in ERAS)
judge('V1_pre_settlement_overnight_leg', res1, hits, diagnostic=diag); print(diag, flush=True)
# ---- V2 size-scaled ridge penalty
RID = [r['id'] for r in rows]; MON = np.array([r['date'][:7] for r in rows]); YV = np.array([FR[i][0] for i in RID]); STOP = np.array([FR[i][1] for i in RID])
F24 = np.array([r['f'] for r in rows], float); MONTHS = sorted(set(MON)); CUT = [(int(np.searchsorted(MON, m, 'left')), int(np.searchsorted(MON, m, 'right'))) for m in MONTHS]
def pipe(lamf):
    PRv = np.full(len(rows), np.nan)
    for a, b in CUT:
        if a < 500 or b == a: continue
        Xt = F24[:a]; mu, sd = Xt.mean(0), Xt.std(0); sd[sd == 0] = 1; S = np.c_[np.ones(a), (Xt - mu) / sd]; pen = np.eye(25) * lamf(a); pen[0, 0] = 0
        bt = np.linalg.solve(S.T @ S + pen, S.T @ YV[:a]); PRv[a:b] = np.c_[np.ones(b - a), (F24[a:b] - mu) / sd] @ bt
    G = {}; hist = []
    for k in range(len(rows)):
        p = PRv[k]
        if np.isnan(p): continue
        a_ = len(hist) >= 100 and p < np.quantile(hist[-252:], 1 / 3); b_ = p - 1.25 / STOP[k] <= 0
        G[RID[k]] = 0.0 if (a_ or b_) else 1.0; hist.append(p)
    return G
assert pipe(lambda n: 100.0) == G3
G2 = pipe(lambda n: 0.2 * n); w = wfast(G2); res2 = {e: full(ret2(e, w[e])) for e in ERAS}
judge('V2_size_scaled_ridge_penalty', res2, luck(G2), last_penalty=round(0.2 * CUT[-1][0], 1), agree_with_G3=round(float(np.mean([G2[i] == G3[i] for i in G3])), 3))
for k in OUT:
    if k != 'G3':
        r = OUT[k]['result']; OUT[k]['clears_noise_floor'] = bool(r['databento']['cagr_pct'] - REF['databento']['cagr_pct'] >= 3 and r['lockbox2010']['cagr_pct'] - REF['lockbox2010']['cagr_pct'] >= 1.5)
        OUT[k]['adopt'] = bool(OUT[k]['adopt_candidate'] and OUT[k]['clears_noise_floor'])
json.dump(OUT, open(f'{A}/batch31.json', 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
print({k: (v.get('adopt'), v.get('clears_noise_floor')) for k, v in OUT.items() if k != 'G3'})
