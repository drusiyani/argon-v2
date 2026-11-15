"""Batch 24 (15 Nov 2026). Rules and marks: analysis/BATCH24_PREREG.md (committed before this file ran).
Needs the batch 14 cache and analysis/_cache/batch24_{era}.pkl from batch24_dump.py."""
import os, json, pickle
A = os.path.dirname(os.path.abspath(__file__))
exec(open(f'{A}/batch14.py').read().split('# ---- Part A')[0])
C24 = {e: pickle.load(open(f'{A}/_cache/batch24_{e}.pkl', 'rb')) for e in ERAS}
key = lambda t: (t['date'], t['strat'], t['variant'], t['entry_min'])
KEY = {t['id']: key(t) for e in ERAS for t in E[e]['tr']}
def flag(g, t): return C24[t['id'][0]]['flags'].get(KEY[t['id']], {}).get(g, False)
SO = {i: (0.0 if m == 0.5 else 1.0) for i, m in W1m.items()}
# ---- G3: walk-forward ridge on friction-free R, monthly, trailing-252 thirds + friction hurdle
FR = {}
for r in NQ:
    t = E[r['id'][0]]['tr'][r['id'][1]]; v = C24[r['id'][0]]['free_R'].get(KEY[r['id']])
    if v is not None and r['f'] is not None: FR[r['id']] = (v, t['risk_pts'], t['entry_min'])
rows = sorted([r for r in NQ if r['id'] in FR], key=lambda r: (r['date'], FR[r['id']][2]))
PRED = {}
for P_ in sorted({r['date'][:7] for r in rows}):
    trn = [r for r in rows if r['date'][:7] < P_]; tst = [r for r in rows if r['date'][:7] == P_]
    if len(trn) < 500 or not tst: continue
    X = np.array([r['f'] for r in trn]); y = np.array([FR[r['id']][0] for r in trn]); mu, sd = X.mean(0), X.std(0); sd[sd == 0] = 1
    S = np.c_[np.ones(len(X)), (X - mu) / sd]; pen = np.eye(X.shape[1] + 1) * 100.0; pen[0, 0] = 0; b = np.linalg.solve(S.T @ S + pen, S.T @ y)
    for r in tst: PRED[r['id']] = float(np.r_[1.0, (np.array(r['f']) - mu) / sd] @ b)
G3 = {}; hist = []; G3why = collections.Counter()
for r in rows:
    if r['id'] not in PRED: continue
    p = PRED[r['id']]; a_ = len(hist) >= 100 and p < np.quantile(hist[-252:], 1 / 3); b_ = p - 1.25 / FR[r['id']][1] <= 0
    G3[r['id']] = 0.0 if (a_ or b_) else 1.0; G3why[('A' if a_ else '') + ('B' if b_ else '') or 'keep'] += 1; hist.append(p)
# ---- vectorised package returns per era
Q = {}
for e in ERAS:
    z = E[e]['z']; days = E[e]['days']; di = {d: k for k, d in enumerate(days)}; tr = [t for t in E[e]['tr'] if t['date'] in di]
    Q[e] = dict(tr=tr, day=np.array([di[t['date']] for t in tr]), nr=np.array([net(t) for t in tr]), nd=len(days), risk=z['risk'],
                base=np.array([E[e]['core'][d] + z['tb'][d] for d in days]), yr=np.array([int(t['date'][:4]) for t in tr]),
                mom=np.array([mom(t) and t['sym'] == 'NQ' for t in tr]), strat=np.array([t['strat'] for t in tr]))
def ret(e, w): q = Q[e]; return q['base'] + 0.5 * q['risk'] * np.bincount(q['day'], weights=w * q['nr'], minlength=q['nd'])
def cagr(r): return 100 * (np.prod(1 + r) ** (252 / len(r)) - 1)
def full(r): return dict(metrics(list(r)), boot=boot(list(r)))
def wvec(e, mult=None, skip=None):
    out = np.ones(len(Q[e]['tr']))
    for i, t in enumerate(Q[e]['tr']):
        if mult is not None and Q[e]['mom'][i]: out[i] = mult.get(t['id'], 1.0)
        if skip is not None and Q[e]['mom'][i] and skip(t): out[i] = 0.0
    return out
def strict(h, b): return bool(h['cagr_pct'] > b['cagr_pct'] and h['sortino'] > b['sortino'] and h['worst_drop_pct'] >= b['worst_drop_pct'] - 1 and h['boot'] <= b['boot'] + 1)
BASE = {e: full(ret(e, wvec(e))) for e in ERAS}; SKIPO = {e: full(ret(e, wvec(e, SO))) for e in ERAS}
ELIG = {'G1': ('quantlab', 'noiseband', 'atrband'), 'G2': ('quantlab', 'noiseband', 'atrband'), 'G4': ('noiseband', 'atrband'), 'G5': ('quantlab',)}
rng = np.random.default_rng(20261115); N = 5000; RES = collections.OrderedDict()
for g in ('G1', 'G2', 'G4', 'G5'):
    alone = {e: full(ret(e, wvec(e, None, lambda t: flag(g, t)))) for e in ERAS}; stack = {e: full(ret(e, wvec(e, SO, lambda t: flag(g, t)))) for e in ERAS}
    m1 = all(strict(alone[e], BASE[e]) for e in ERAS)
    m3 = all(stack[e]['cagr_pct'] > SKIPO[e]['cagr_pct'] and stack[e]['sortino'] > SKIPO[e]['sortino'] and stack[e]['worst_drop_pct'] >= SKIPO[e]['worst_drop_pct'] - 1 for e in ERAS)
    hits = 0; target = {e: cagr(ret(e, wvec(e, None, lambda t: flag(g, t)))) for e in ERAS}
    grp = {e: [] for e in ERAS}; nskip = {e: {} for e in ERAS}
    for e in ERAS:
        el = np.array([Q[e]['mom'][i] and Q[e]['strat'][i] in ELIG[g] for i in range(len(Q[e]['tr']))]); fl = np.array([flag(g, t) if el[i] else False for i, t in enumerate(Q[e]['tr'])])
        for y in sorted(set(Q[e]['yr'])):
            idx = np.where(el & (Q[e]['yr'] == y))[0]; k = int(fl[idx].sum())
            if k: grp[e].append((idx, k))
    for _ in range(N):
        ok = True
        for e in ERAS:
            w = np.ones(len(Q[e]['tr']))
            for idx, k in grp[e]: w[rng.choice(idx, k, replace=False)] = 0.0
            ok &= cagr(ret(e, w)) >= target[e]
        hits += ok
    sk = {}
    for lab, a, b in (('2010-13', '2010', '2014'), ('2014-17', '2014', '2018'), ('2018-20', '2018', '2021'), ('2021-25', '2021', '2026'), ('2026', '2026', '2027')):
        ts = [t for e in ERAS for t in Q[e]['tr'] if a <= t['date'] < b and t['strat'] in ELIG[g] and t['sym'] == 'NQ' and mom(t)]
        s_ = [net(t) for t in ts if flag(g, t)]; k_ = [net(t) for t in ts if not flag(g, t)]
        sk[lab] = dict(skipped=len(s_), skipped_avg_R=round(float(np.mean(s_)), 3) if s_ else None, kept_avg_R=round(float(np.mean(k_)), 3) if k_ else None)
    RES[g] = dict(alone=alone, on_skip_only=stack, mark1_strict_alone=bool(m1), mark2_luck_random_beating_both_eras=int(hits), mark2_pass=bool(hits / N < 0.05),
                  mark3_on_skip_only=bool(m3), adopt_candidate=bool(m1 and hits / N < 0.05 and m3), skipped_vs_kept=sk)
# ---- G3 vs skip-only
g3 = {e: full(ret(e, wvec(e, G3))) for e in ERAS}; g3_strict = all(strict(g3[e], SKIPO[e]) for e in ERAS)
by = collections.defaultdict(list)
for r in rows:
    if r['id'] in G3: by[r['date'][:4]].append(r['id'])
hits = 0; tgt = {e: cagr(ret(e, wvec(e, G3))) for e in ERAS}; ids = {e: {t['id']: i for i, t in enumerate(Q[e]['tr'])} for e in ERAS}
for _ in range(N):
    sh = {}
    for y, L in by.items(): v = [G3[i] for i in L]; rng.shuffle(v); sh.update(zip(L, v))
    hits += all(cagr(ret(e, wvec(e, sh))) >= tgt[e] for e in ERAS)
def gap(pred_map, a, b):
    rr = [r for r in rows if a <= r['date'] < b and r['id'] in pred_map]
    if len(rr) < 30: return None
    p = np.array([pred_map[r['id']] for r in rr]); y = np.array([r['y'] for r in rr]); lo, hi = np.quantile(p, [1 / 3, 2 / 3])
    return round(float(y[p > hi].mean() - y[p < lo].mean()), 3)
def gapW(a, b):
    rr = [r for r in rows if a <= r['date'] < b and r['id'] in W1m]; t_ = [r['y'] for r in rr if W1m[r['id']] == 1.5]; b_ = [r['y'] for r in rr if W1m[r['id']] == 0.5]
    return round(float(np.mean(t_) - np.mean(b_)), 3) if t_ and b_ else None
diag3 = {lab: dict(G3_gross_model=gap(PRED, a, b), W1m=gapW(a, b)) for lab, a, b in (('2012-13', '2012', '2014'), ('2014-17', '2014', '2018'), ('2018-20', '2018', '2021'), ('2021-26', '2021', '2027'))}
skips = {e: round(1 - np.mean([G3.get(t['id'], 1.0) for t in Q[e]['tr'] if t['id'] in G3]), 3) for e in ERAS}
RES['G3'] = dict(result=g3, skip_only=SKIPO, strict_vs_skip_only=bool(g3_strict), luck_random_beating_both_eras=int(hits), luck_pass=bool(hits / N < 0.05),
                 adopt_candidate=bool(g3_strict and hits / N < 0.05), skip_share=skips, why=dict(G3why), ranking_gap_within_period=diag3)
json.dump(dict(baseline=BASE, skip_only=SKIPO, results=RES), open(f'{A}/batch24.json', 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
fmt = lambda h: f"{h['cagr_pct']:5.1f} {h['sortino']:4.2f} {h['worst_drop_pct']:6.1f} {h['boot']:5.1f}"
print('package   ', ' | '.join(fmt(BASE[e]) for e in ERAS)); print('skip-only ', ' | '.join(fmt(SKIPO[e]) for e in ERAS))
for g in ('G1', 'G2', 'G4', 'G5'):
    r = RES[g]; print(g, 'alone', ' | '.join(fmt(r['alone'][e]) for e in ERAS), '| on skip-only', ' | '.join(fmt(r['on_skip_only'][e]) for e in ERAS), '| m1', r['mark1_strict_alone'], 'luck', r['mark2_luck_random_beating_both_eras'], 'm3', r['mark3_on_skip_only'], 'ADOPT' if r['adopt_candidate'] else '')
    print('   ', r['skipped_vs_kept'])
r = RES['G3']; print('G3', ' | '.join(fmt(r['result'][e]) for e in ERAS), 'strict vs skip-only', r['strict_vs_skip_only'], 'luck', r['luck_random_beating_both_eras'], 'skip share', r['skip_share'], r['why'], 'ADOPT' if r['adopt_candidate'] else '')
print('   ', diag3)
