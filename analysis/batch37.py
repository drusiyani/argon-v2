"""Batch 37 (descriptive, changes nothing): days like 23 Nov 2026 - a big gap up the morning after a heavy selloff,
then a whipsaw. Lists matching days and what the session did. NQ regular hours, contract-roll days left out."""
import os, sys, json
A = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(A)
sys.path.insert(0, os.path.join(ROOT, 'research'))
import common as c
ERA = c.DATA

def main():
    T, O, H, L, C, n, mins, days, wd = c.prep('NQ'); D, dl, atr = c.daily('NQ'); R = c.roll('NQ')
    rows = []
    for k in range(6, len(dl)):
        d = dl[k]; p = D[dl[k - 1]]; x = D[d]
        if d in R or dl[k - 1] in R: continue
        gap = x['o'] / p['c'] - 1; prior5 = p['c'] / D[dl[k - 6]]['c'] - 1
        if gap < 0.015 or prior5 > -0.04: continue
        first = [i for i in x['r'] if mins[i] < 600]; after = [i for i in x['r'] if mins[i] >= 600]
        lo30 = min(L[i] for i in first) / x['o'] - 1
        lo_i = min(first, key=lambda i: L[i]); hi_after = max(H[i] for i in x['r'] if i > lo_i) / x['o'] - 1
        shape = abs(x['c'] - x['o']) / (x['h'] - x['l'])
        rows.append(dict(date=d, gap_pct=round(gap * 100, 2), prior5_pct=round(prior5 * 100, 2), first30_low_pct=round(lo30 * 100, 2),
                         high_after_low_pct=round(hi_after * 100, 2), close_vs_open_pct=round((x['c'] / x['o'] - 1) * 100, 2),
                         trend_day=shape >= 0.6,
                         whipsaw=lo30 <= -0.01 and hi_after >= 0.005 and shape < 0.6))
    json.dump(dict(era=ERA, rule='gap up >= 1.5% at the open after the previous 5 sessions fell >= 4%', days=rows),
              open(f'{A}/batch37_{ERA}.json', 'w'), indent=1)
    print(len(rows), sum(r['whipsaw'] for r in rows))

main()
