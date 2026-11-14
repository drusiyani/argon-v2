"""Batch 20 (14 Nov 2026). What is tested and how it is read: analysis/BATCH20_PREREG.md (committed before this file ran)."""
import os, json
A = os.path.dirname(os.path.abspath(__file__))
exec(open(f'{A}/batch14.py').read().split('# ---- Part A')[0])
rng = np.random.default_rng(20261114); N = 20000
S = {i: (0.0 if m == 0.5 else 1.0) for i, m in W1m.items()}; H = {i: (0.0 if m == 0.5 else m) for i, m in W1m.items()}
Q = {}
for e in ERAS:
    z = E[e]['z']; days = E[e]['days']; di = {d: k for k, d in enumerate(days)}; tr = [t for t in E[e]['tr'] if t['date'] in di]
    sized = np.array([t['id'] in W1m for t in tr]); yr = np.array([int(t['date'][:4]) for t in tr])
    Q[e] = dict(day=np.array([di[t['date']] for t in tr]), nr=np.array([net(t) for t in tr]), nd=len(days), risk=z['risk'],
                base=np.array([E[e]['core'][d] + z['tb'][d] for d in days]), idx=np.array([z['ret'][d] for d in days]),
                mS=np.array([S.get(t['id'], 1.0) for t in tr]), mH=np.array([H.get(t['id'], 1.0) for t in tr]),
                groups=[np.where(sized & (yr == y))[0] for y in sorted(set(yr[sized]))])
def st(r):
    eq = np.cumprod(1 + r); peak = np.maximum.accumulate(np.concatenate([[1.0], eq]))[1:]
    return (100 * (eq[-1] ** (252 / len(r)) - 1), r.mean() / np.sqrt(np.mean(np.minimum(0, r) ** 2)) * np.sqrt(252), 100 * min(0.0, float((eq / peak - 1).min())))
def ret(e, w): q = Q[e]; return q['base'] + 0.5 * q['risk'] * np.bincount(q['day'], weights=w * q['nr'], minlength=q['nd'])
BASE = {e: st(ret(e, np.ones(len(Q[e]['nr'])))) for e in ERAS}; IDXDD = {e: st(Q[e]['idx'])[2] for e in ERAS}
MODEL = {k: {e: st(ret(e, Q[e][m])) for e in ERAS} for k, m in (('skip-only', 'mS'), ('skip-and-press', 'mH'))}
def passes(k, e, s):
    b = BASE[e]; better = s[0] > b[0] and s[1] > b[1]
    return better and (s[2] >= b[2] - 1 if k == 'skip-only' else (s[2] >= b[2] - 5 and s[2] >= IDXDD[e]))
luck = {}
for k, m in (('skip-only', 'mS'), ('skip-and-press', 'mH')):
    beat_ret = beat_sort = mark = 0; per = {e: 0 for e in ERAS}; pm = {e: 0 for e in ERAS}; mean = {e: 0.0 for e in ERAS}
    for _ in range(N):
        ok_r = ok_s = ok_m = True
        for e in ERAS:
            w = Q[e][m].copy()
            for g in Q[e]['groups']: w[g] = w[g][rng.permutation(len(g))]
            s = st(ret(e, w)); mean[e] += s[0] / N
            r_ = s[0] >= MODEL[k][e][0]; per[e] += r_; ok_r &= r_; ok_s &= s[1] >= MODEL[k][e][1]; p_ = passes(k, e, s); pm[e] += p_; ok_m &= p_
        beat_ret += ok_r; beat_sort += ok_s; mark += ok_m
    p = beat_ret / N; p_up = max(beat_ret, 3) / N        # with 0 hits, 3/N is the usual 95% upper bound
    luck[k] = dict(model={e: [round(v, 2) for v in MODEL[k][e]] for e in ERAS}, random_mean_return={e: round(mean[e], 1) for e in ERAS},
                   random_beats_model_return_each_era={e: per[e] for e in ERAS}, random_beats_model_return_both_eras=int(beat_ret), random_beats_model_sortino_both_eras=int(beat_sort),
                   random_passes_mark_each_era={e: pm[e] for e in ERAS}, random_passes_mark_both_eras=int(mark), draws=N,
                   best_of_230_beats_model_pct=round(100 * (1 - (1 - p) ** 230), 2), best_of_230_upper_bound_pct=round(100 * (1 - (1 - p_up) ** 230), 2),
                   best_of_230_passes_mark_pct=round(100 * (1 - (1 - mark / N) ** 230), 1),
                   reading='unlikely to be search luck' if (1 - (1 - p_up) ** 230) < 0.05 else ('unlikely to be search luck (point estimate), upper bound above 5%' if (1 - (1 - p) ** 230) < 0.05 else 'could be search luck'))
# ---- Part 2: QuantLab direction, from entry (not from the open)
ql = collections.defaultdict(list); cost = collections.defaultdict(list)
for e in ERAS:
    z = E[e]['z']
    for t in E[e]['tr']:
        if t['date'] not in E[e]['ds'] or t['sym'] != 'NQ' or not mom(t): continue
        cost[t['date'][:4]].append(t['cost'])
        if t['strat'] != 'quantlab' or 'entry' not in t: continue
        s = 1 if t['side'] in (1, 'long') else -1; o, h, l, cl = z['D'][t['date']]
        ql[t['date'][:4]].append((s * (cl - o) > 0, s * (cl - t['entry']) > 0, s * (cl - t['entry']) / t['risk_pts'], t['gross']))
part2 = {y: dict(trades=len(v), right_incl_first_candle_pct=round(100 * np.mean([a for a, _, _, _ in v]), 1), right_from_entry_pct=round(100 * np.mean([b for _, b, _, _ in v]), 1),
                 hold_to_close_no_stop_avg_R=round(float(np.mean([c_ for _, _, c_, _ in v])), 3), actual_avg_gross_R=round(float(np.mean([g for _, _, _, g in v])), 3)) for y, v in sorted(ql.items())}
part3 = {y: dict(trades=len(v), avg_cost_R=round(float(np.mean(v)), 4)) for y, v in sorted(cost.items())}
json.dump(dict(baseline={e: [round(v, 2) for v in BASE[e]] for e in ERAS}, part1_search_luck=luck, part2_quantlab_direction=part2, part3_cost_in_R=part3), open(f'{A}/batch20.json', 'w'), indent=1, default=lambda o: o.item())
print('base', BASE); print(json.dumps(luck, indent=1, default=lambda o: o.item()))
for y, v in part2.items(): print(y, v, part3[y])
