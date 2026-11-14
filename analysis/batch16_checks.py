"""Batch 16 diagnostics (no pass mark): luck check for skip-only, and how it does in each sub-period."""
import os, json, random
A = os.path.dirname(os.path.abspath(__file__))
exec(open(f'{A}/batch16.py').read().split('B0 = {e:')[0])
by = collections.defaultdict(list)
for r in NQ:
    if r['id'] in R2: by[r['date'][:4]].append(r['id'])
rng = random.Random(7); sims = {e: [] for e in ERAS}; real = {e: metrics(series(e, R2)) for e in ERAS}
for _ in range(300):
    sh = {}
    for y, ids in by.items(): v = [R2[i] for i in ids]; rng.shuffle(v); sh.update(zip(ids, v))
    for e in ERAS: sims[e].append(metrics(series(e, sh)))
luck = {e: dict(model_cagr=real[e]['cagr_pct'], shuffled_mean_cagr=round(sum(s['cagr_pct'] for s in sims[e]) / 300, 1), shuffles_beating_model_on_return=sum(s['cagr_pct'] >= real[e]['cagr_pct'] for s in sims[e]),
                model_sortino=real[e]['sortino'], shuffles_beating_model_on_sortino=sum(s['sortino'] >= real[e]['sortino'] for s in sims[e])) for e in ERAS}
SUBS = (('2013-17 (no edge)', 'lockbox2010', '2013', '2018'), ('2018-20', 'lockbox2010', '2018', '2021'), ('2021-25', 'databento', '2021', '2026'), ('2026 so far', 'databento', '2026', '2027'))
def sub(e, a, b, mult):
    x = [v for v, d in zip(series(e, mult), E[e]['days']) if a <= d < b]; m = metrics(x); return f"{m['cagr_pct']:+.1f}% / {m['worst_drop_pct']:.1f}%"
core_only = {i: 0.0 for e in ERAS for i in [t['id'] for t in E[e]['tr']]}
def core_series(e, a, b):
    z = E[e]['z']; x = [E[e]['core'][d] + z['tb'][d] for d in E[e]['days'] if a <= d < b]; m = metrics(x); return f"{m['cagr_pct']:+.1f}% / {m['worst_drop_pct']:.1f}%"
table = {'core only (no rules)': {lab: core_series(e, a, b) for lab, e, a, b in SUBS}}
for nm, mult in (('package today', None), ('skip-only (R2)', R2), ('cut-only (R1)', R1), ('model x0.5/x1/x1.5', W1m)): table[nm] = {lab: sub(e, a, b, mult) for lab, e, a, b in SUBS}
json.dump(dict(luck_check_skip_only=luck, sub_periods=table), open(f'{A}/batch16_checks.json', 'w'), indent=1); print(json.dumps(luck)); [print(f'{k:24s}', v) for k, v in table.items()]
