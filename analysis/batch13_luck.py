"""Batch 13 diagnostic (no pass mark): is the walk-forward model's gain skill or just luck / extra size?
The model's own multipliers are shuffled among that year's trades 300 times (same sizes, same counts, random trades)."""
import os, sys, json, random, collections
sys.argv = [sys.argv[0]]; A = os.path.dirname(os.path.abspath(__file__))
src = open(f'{A}/batch13.py').read().split("mk = lambda")[0]; exec(src)
ids_by_year = collections.defaultdict(list)
for r in ROWS:
    if r['id'] in W['W1']: ids_by_year[r['date'][:4]].append(r['id'])
real = {e: metrics(series(e, capped(W['W1'])))['cagr_pct'] for e in ERAS}; rng = random.Random(7); sims = {e: [] for e in ERAS}
for _ in range(300):
    sh = {}
    for y, ids in ids_by_year.items():
        v = [W['W1'][i] for i in ids]; rng.shuffle(v); sh.update(zip(ids, v))
    for e in ERAS: sims[e].append(metrics(series(e, capped(sh)))['cagr_pct'])
out = {e: dict(baseline=B0[e]['cagr_pct'], model=real[e], shuffled_mean=round(sum(sims[e]) / 300, 1), shuffled_best=max(sims[e]), shuffles_beating_model=sum(s >= real[e] for s in sims[e])) for e in ERAS}
avgw = {e: round(sum(W['W1'].get(t['id'], 1.0) for t in E[e]['tr'] if mom(t) and t['date'] in E[e]['ds']) / sum(1 for t in E[e]['tr'] if mom(t) and t['date'] in E[e]['ds']), 3) for e in ERAS}
json.dump(dict(luck_check=out, avg_multiplier=avgw), open(f'{A}/batch13_luck.json', 'w'), indent=1); print(out, avgw)
