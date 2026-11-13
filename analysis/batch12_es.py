"""Batch 12 addendum: replication of the day-after and gap-and-yesterday patterns on the S&P future (ES). See BATCH12_PREREG.md."""
import os, sys, json, collections, statistics
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'engine'))
import portfolio as P
c = P.c; ERA = os.environ.get('ARGON_DATA', 'databento'); cap = P.CONFIG['cost_cap_R']; kw = P.CONFIG['strategies']
LO, HI = (('2021-01-01', '2026-12-31') if ERA == 'databento' else ('2010-07-01', '2020-12-31'))
tr = c.walkforward(c.quantlab('ES', **kw['quantlab'])) + c.walkforward(c.noiseband('ES', **kw['noiseband'])) + c.atrband('ES', **kw['atrband'])
tr = [t for t in tr if t['cost'] <= cap and LO <= t['date'] <= HI]
D, dl, atr = c.daily('ES'); pos = {d: k for k, d in enumerate(dl)}; first = min(t['date'] for t in tr); days = [d for d in dl[1:] if max(LO, first) <= d <= HI]
R = collections.defaultdict(float)
for t in tr: R[t['date']] += t['gross'] - t['cost']
per = lambda d: '2010-17' if d < '2018' else ('2018-20' if d < '2021' else '2021-26')
out = {'era': ERA, 'trades': len(tr), 'total_R': round(sum(R.values()), 1), 'day_after': {}, 'gap_and_yesterday': {}}
A = collections.defaultdict(list); B = collections.defaultdict(list)
for i in range(1, len(days)):
    d, p = days[i], days[i - 1]; A[(per(d), 'after win > 2R' if R.get(p, 0.0) > 2 else 'other days')].append(R.get(d, 0.0))
for t in tr:
    k = pos.get(t['date'], 0)          # half-day sessions have no daily bar: skipped (fixed before any result was seen)
    if k == 0: continue
    p = dl[k - 1]; s = 1 if t['side'] in (1, 'long') else -1; g = (D[t['date']]['o'] - D[p]['c']) * s; y = (D[p]['c'] - D[p]['o']) * s
    lab = 'with gap, against yesterday' if (g > 0 and y < 0) else ('against gap, with yesterday' if (g < 0 and y > 0) else 'other')
    B[(per(t['date']), lab)].append(t['gross'] - t['cost'])
for (p, lab), v in sorted(A.items()): out['day_after'][f'{p} | {lab}'] = dict(days=len(v), avg_R_per_day=round(statistics.mean(v), 3))
for (p, lab), v in sorted(B.items()): out['gap_and_yesterday'][f'{p} | {lab}'] = dict(trades=len(v), avg_R=round(statistics.mean(v), 3))
json.dump(out, open(os.path.join(ROOT, 'analysis', f'batch12_es_{ERA}.json'), 'w'), indent=1); print(json.dumps(out, indent=1))
