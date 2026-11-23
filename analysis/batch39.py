"""Batch 39: intraday safety stop on the core (rules: analysis/BATCH39_PREREG.md)."""
import os, sys, json, math, csv, bisect, collections, statistics as stt
A = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(A)
sys.path.insert(0, A); sys.path.insert(0, os.path.join(ROOT, 'research')); sys.path.insert(0, os.path.join(ROOT, 'engine'))
import common as c
from batch38 import rules_daily, stats
ERA = c.DATA; TICK = 0.25

def main():
    T, O, H, L, C, n, mins, days, wd = c.prep('NQ'); D, dl, _ = c.daily('NQ'); R = c.roll('NQ')
    idx = collections.defaultdict(list)
    for i in range(n):
        if mins[i] < 960 or mins[i] >= 1080: idx[days[i]].append(i)
    V = {}
    for row in csv.DictReader(open(os.path.join(ROOT, 'analysis', 'vxn.csv'))):
        try: V[row['date']] = float(row['vxn'])
        except ValueError: pass
    vk = sorted(V); rd = rules_daily()
    names = ('current', 'stop 1.5%', 'stop 2%', 'stop 3%'); S = {'stop 1.5%': .015, 'stop 2%': .02, 'stop 3%': .03}
    rows = {k: dict(book=[], core=[]) for k in names}; fired = collections.Counter(); recovered = collections.Counter()
    for k in range(260, len(dl)):
        d, p = dl[k], dl[k - 1]; i = bisect.bisect_left(vk, p)
        if i == 0: continue
        v = V[vk[i - 1]]; hist = sorted(V[x] for x in vk[max(0, i - 252):i]); w = min(1.5, hist[len(hist) // 2] / v)
        roll = d in R or p in R; pc = D[p]['c']; cl = D[d]['c']
        base = (cl / D[d]['o'] - 1) if roll else (cl / pc - 1)
        if abs(base) > 0.15: base = 0.0
        for name in names:
            r = base
            if name != 'current' and not roll:
                stop = pc * (1 - S[name])
                for j in idx[d]:
                    if L[j] <= stop:
                        fill = min(stop, O[j]) - 2 * TICK; r = fill / pc - 1; fired[name] += 1
                        if cl > stop: recovered[name] += 1
                        break
            rows[name]['core'].append(w * r); rows[name]['book'].append(w * r + rd.get(d, 0.0))
    out = dict(era=ERA, period=[dl[260], dl[-1]], variants={})
    for name in names:
        out['variants'][name] = dict(book=stats(rows[name]['book']), core=stats(rows[name]['core']), stop_fired=fired[name],
                                     closed_above_stop_after=recovered[name])
        print(name, out['variants'][name], flush=True)
    json.dump(out, open(f'{A}/batch39_{ERA}.json', 'w'), indent=1)

if __name__ == '__main__': main()
