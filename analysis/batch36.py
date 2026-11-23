"""Batch 36 (descriptive, changes nothing): how often is Opening Drive stopped out early and the market then runs a long
way in the direction it called (as on 23 Nov 2026)? Counts the live rule's own trades (monthly re-pick, cost rule)."""
import os, sys, json, bisect, collections
A = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(A)
sys.path.insert(0, os.path.join(ROOT, 'research')); sys.path.insert(0, os.path.join(ROOT, 'engine'))
import common as c
from portfolio import CONFIG
ERA = c.DATA

def main():
    T, O, H, L, C, n, mins, days, wd = c.prep('NQ')
    first = {}
    for i in range(n):
        if days[i] not in first: first[days[i]] = i
    tr = [t for t in c.walkforward(c.quantlab('NQ', **CONFIG['strategies']['quantlab']), 1.0) if t['cost'] <= CONFIG['cost_cap_R']]
    out = dict(era=ERA, trades=len(tr), stopped=0, early_stop=0, runs={k: 0 for k in (2, 5, 10, 20)}, examples=[])
    for t in tr:
        net = t['gross'] - t['cost']
        if t['gross'] > -0.95: continue                     # not a full stop-out
        out['stopped'] += 1
        if t['exit_min'] >= 600: continue                   # "early" = stopped before 10:00
        out['early_stop'] += 1
        i = first[t['date']]; best = 0.0
        while i < n and days[i] == t['date']:
            if mins[i] >= t['exit_min'] and mins[i] < 960:
                best = max(best, (H[i] - t['entry']) if t['side'] == 1 else (t['entry'] - L[i]))
            i += 1
        run = best / t['risk_pts']
        for k in out['runs']:
            if run >= k: out['runs'][k] += 1
        if run >= 10: out['examples'].append([t['date'], round(t['risk_pts'], 2), round(run, 1)])
    out['examples'] = out['examples'][-15:]
    json.dump(out, open(f'{A}/batch36_{ERA}.json', 'w'), indent=1); print(json.dumps(out))

main()
