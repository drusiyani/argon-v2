"""Analysis only (does not touch the race). Four published Nasdaq-futures edges, tested unchanged on both eras.
Pass mark fixed BEFORE the run (11 Nov 2026): mean return > 0 AND Sharpe >= 0.3 in BOTH eras (2011-20 and 2021-26).
Costs: 0.75 NQ points per round trip (Argon's cost), charged on every entry. Sized 1x the contract value when in.
  E1 Overnight hold: long at the 16:00 close, out at the next 9:30 open.
  E2 Overnight reversal (CO-OC): at 9:30, short to 16:00 if the overnight move was up, long if it was down.
  E3 Turn of the month: long from the close of the day before the month's last trading day to the close of the 3rd trading day.
  E4 Pre-FOMC: long from the close the day before a scheduled Fed decision to 13:59 on decision day.
Roll days are skipped. Also reported: correlation with Argon's book, day by day."""
import os, sys, json, math, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'engine'))
import portfolio as P
c = P.c
ERA = os.environ.get('ARGON_DATA', 'databento'); COST = c.COST['NQ']
D, dl, _ = c.daily('NQ'); T, O, H, L, C, n, mins, days, wd = c.prep('NQ')
skip = set()
for f in ('roll', 'bad_days'):
    try:
        v = getattr(c, f)('NQ'); v = v.keys() if isinstance(v, dict) else v; skip |= {x for x in v if isinstance(x, str) and len(x) == 10}
    except Exception: pass
lo = '2021-01-01' if ERA == 'databento' else '2010-07-01'; hi = '2026-12-31' if ERA == 'databento' else '2020-12-31'
dl = [d for d in dl if lo <= d <= hi]
def bad(*ds): return any(d in skip for d in ds)
E = {k: collections.defaultdict(float) for k in ('E1 overnight hold', 'E2 overnight reversal', 'E3 turn of month', 'E4 pre-FOMC')}
for k in range(1, len(dl)):
    d, p = dl[k], dl[k - 1]
    if bad(d, p): continue
    on = D[d]['o'] / D[p]['c'] - 1
    if abs(on) < 0.15: E['E1 overnight hold'][d] += on - COST / D[p]['c']
    if on != 0: E['E2 overnight reversal'][d] += -math.copysign(1, on) * (D[d]['c'] / D[d]['o'] - 1) - COST / D[d]['o']
last = [k for k in range(len(dl) - 1) if dl[k][:7] != dl[k + 1][:7]]
for k in last:
    a, b = k - 1, k + 3
    if a < 0 or b >= len(dl) or bad(*dl[a:b + 1]): continue
    E['E3 turn of month'][dl[b]] += D[dl[b]]['c'] / D[dl[a]]['c'] - 1 - COST / D[dl[a]]['c']
pos = {d: k for k, d in enumerate(dl)}
for d in sorted(c.FOMC):
    if d not in pos or pos[d] == 0: continue
    p = dl[pos[d] - 1]
    if bad(d, p): continue
    i2 = [i for i in D[d]['r'] if mins[i] <= 839]
    if not i2: continue
    E['E4 pre-FOMC'][d] += C[i2[-1]] / D[p]['c'] - 1 - COST / D[p]['c']
book = collections.defaultdict(float)
for t in P.book(1.0): book[t['date']] += t['w'] * (t['gross'] - t['cost'])
idx = {dl[k]: (0.0 if bad(dl[k], dl[k - 1]) else D[dl[k]]['c'] / D[dl[k - 1]]['c'] - 1) for k in range(1, len(dl))}

def stats(ser):
    x = [ser.get(d, 0.0) for d in dl[1:]]; m = sum(x) / len(x); s = math.sqrt(sum((v - m) ** 2 for v in x) / (len(x) - 1)) or 1
    eq = 1.0; peak = 1.0; dd = 0.0
    for v in x: eq *= 1 + v; peak = max(peak, eq); dd = min(dd, eq / peak - 1)
    held = [v for d, v in ser.items()]; hm = sum(held) / len(held) if held else 0
    hs = math.sqrt(sum((v - hm) ** 2 for v in held) / (len(held) - 1)) if len(held) > 1 else 1
    b = [book.get(d, 0.0) for d in dl[1:]]; mb = sum(b) / len(b)
    cov = sum((u - m) * (w - mb) for u, w in zip(x, b)); vb = sum((w - mb) ** 2 for w in b)
    return dict(times_traded=len(held), avg_per_trade_pct=round(100 * hm, 3), t_stat=round(hm / hs * math.sqrt(len(held)), 2) if hs else None,
                final_usd=round(100000 * eq), cagr_pct=round(100 * (eq ** (252 / len(x)) - 1), 1), sharpe=round(m / s * math.sqrt(252), 2),
                worst_drop_pct=round(100 * dd, 1), corr_with_argon=round(cov / math.sqrt(sum((u - m) ** 2 for u in x) * vb), 3) if vb else None)
res = {k: stats(v) for k, v in E.items()}; res['index alone (reference)'] = stats(idx)
out = dict(era=ERA, note=__doc__, range=[dl[1], dl[-1]], results=res)
json.dump(out, open(os.path.join(ROOT, 'analysis', f'edges_{ERA}.json'), 'w'), indent=1)
print(json.dumps(out['results'], indent=1))
