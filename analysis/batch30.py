"""Batch 30: core / rules split under G3. Rules: analysis/BATCH30_PREREG.md (committed before this file ran)."""
import os
A = os.path.dirname(os.path.abspath(__file__)); s29 = open(f'{A}/batch29.py').read()
exec(s29.split('# ---------------------------------------------------------------- U1')[0])
LIM = {'databento': (-35.1, 35.3), 'lockbox2010': (-28.6, 8.3)}; RES = {}
def mix(e, c, k):
    q = Q[e]; z = E[e]['z']; days = E[e]['days']; core = np.array([E[e]['core'][d] for d in days]); tb = np.array([z['tb'][d] for d in days])
    r = c * core + tb + k * q['risk'] * np.bincount(q['day'], weights=WG3[e] * q['nr'], minlength=q['nd']); h = full(r)
    if e == 'databento':
        m = np.array([d >= '2026-01-01' for d in days]); eq = np.cumprod(1 + r[m]); pk = np.maximum.accumulate(np.r_[1.0, eq])[1:]
        h.update(y26_ret=round(100 * (eq[-1] - 1), 1), y26_dd=round(100 * float((eq / pk - 1).min()), 1))
    return h
for c in (0.25, 0.5, 0.75, 1.0):
    for k in (0.5, 0.625, 0.75, 1.0):
        RES[(c, k)] = {e: mix(e, c, k) for e in ERAS}; h = RES[(c, k)]
        print(c, k, ' | '.join(fmt(h[e]) for e in ERAS), '| 2026', h['databento']['y26_ret'], h['databento']['y26_dd'], flush=True)
ref = RES[(1.0, 0.5)]
def ok_strict(h): return all(h[e]['worst_drop_pct'] >= ref[e]['worst_drop_pct'] - 1 and h[e]['boot'] <= ref[e]['boot'] + 1 for e in ERAS)
def ok_growth(h): return all(h[e]['worst_drop_pct'] >= ref[e]['worst_drop_pct'] - 5 and h[e]['worst_drop_pct'] >= LIM[e][0] and h[e]['boot'] <= LIM[e][1] for e in ERAS)
def pick(ok):
    c_ = [m for m, h in RES.items() if ok(h)]; b = max(c_, key=lambda m: min(RES[m][e]['cagr_pct'] for e in ERAS))
    return dict(mix=b, result=RES[b], beats_G3_both_eras=bool(all(RES[b][e]['cagr_pct'] > ref[e]['cagr_pct'] for e in ERAS)))
out = dict(grid={f'core {c} rules {k}': h for (c, k), h in RES.items()}, strict_risk_winner=pick(ok_strict), growth_limit_winner=pick(ok_growth))
json.dump(out, open(f'{A}/batch30.json', 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
print('STRICT', out['strict_risk_winner']['mix'], out['strict_risk_winner']['beats_G3_both_eras']); print('GROWTH', out['growth_limit_winner']['mix'], out['growth_limit_winner']['beats_G3_both_eras'])
