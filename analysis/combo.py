"""Analysis only (does not touch the race). The surviving ideas combined with the existing strategy, on both eras.
Pass marks fixed BEFORE the run (11 Nov 2026):
  FULL PACKAGE (Nasdaq core + rules at half size + pre-FOMC tilt + T-bill interest) passes if, in BOTH eras,
  its Sharpe beats the Nasdaq alone AND its worst drop is no deeper than the Nasdaq alone.
Pieces: core = 1x NQ close to close; rules = Argon's book unchanged, 1% per 1R, at half size; pre-FOMC tilt = an extra
1x long from the close before a scheduled Fed decision to 13:59 on decision day; interest = 3-month T-bill (FRED DTB3,
analysis/tbill_dtb3.csv) on the cash, since futures only tie up margin. Costs 0.75 NQ pts per round trip. Roll days skipped."""
import os, sys, json, math, csv, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'engine'))
import portfolio as P
c = P.c
ERA = os.environ.get('ARGON_DATA', 'databento'); risk = P.CONFIG['risk_pct'] / 100; COST = c.COST['NQ']
D, dl, _ = c.daily('NQ'); T, O, H, L, C, n, mins, days, wd = c.prep('NQ')
skip = set()
for f in ('roll', 'bad_days'):
    try:
        v = getattr(c, f)('NQ'); v = v.keys() if isinstance(v, dict) else v; skip |= {x for x in v if isinstance(x, str) and len(x) == 10}
    except Exception: pass
book = collections.defaultdict(float); first = None
for t in P.book(1.0):
    book[t['date']] += t['w'] * (t['gross'] - t['cost']); first = min(first or t['date'], t['date'])
lo, hi = (('2021-01-01', '2026-12-31') if ERA == 'databento' else ('2010-07-01', '2020-12-31'))
dl = [d for d in dl if max(lo, first) <= d <= hi]
idx = {dl[k]: (0.0 if (dl[k] in skip or dl[k - 1] in skip) else D[dl[k]]['c'] / D[dl[k - 1]]['c'] - 1) for k in range(1, len(dl))}
pos = {d: k for k, d in enumerate(dl)}; fomc = {}
for d in sorted(c.FOMC):
    if d not in pos or pos[d] == 0: continue
    p = dl[pos[d] - 1]
    if d in skip or p in skip: continue
    i2 = [i for i in D[d]['r'] if mins[i] <= 839]
    if i2: fomc[d] = C[i2[-1]] / D[p]['c'] - 1 - COST / D[p]['c']
TB = {r['date']: float(r['dtb3_pct']) / 100 / 252 for r in csv.DictReader(open(os.path.join(ROOT, 'analysis', 'tbill_dtb3.csv')))}
tbd = sorted(TB); tb = {}; j = 0; last = 0.0
for d in dl:
    while j < len(tbd) and tbd[j] <= d: last = TB[tbd[j]]; j += 1
    tb[d] = last
days = dl[1:]
def stats(f):
    eq, peak, dd, yr, x = 1.0, 1.0, 0.0, collections.OrderedDict(), []
    for d in days:
        r = f(d); x.append(r); yr.setdefault(d[:4], eq); eq *= 1 + r; peak = max(peak, eq); dd = min(dd, eq / peak - 1)
    m = sum(x) / len(x); s = math.sqrt(sum((v - m) ** 2 for v in x) / (len(x) - 1)); ys = list(yr)
    return dict(final_usd=round(100000 * eq), cagr_pct=round(100 * (eq ** (252 / len(x)) - 1), 1), sharpe=round(m / s * math.sqrt(252), 2),
                worst_drop_pct=round(100 * dd, 1), years={y: round(100 * ((yr[ys[i + 1]] if i + 1 < len(ys) else eq) / yr[y] - 1), 1) for i, y in enumerate(ys)})
R = lambda d: risk * book.get(d, 0.0)
S = {
 'existing strategy (rules alone)':           lambda d: R(d),
 'existing + pre-FOMC + interest':             lambda d: R(d) + fomc.get(d, 0.0) + tb[d],
 'Nasdaq alone':                               lambda d: idx[d],
 'Nasdaq + half rules':                        lambda d: idx[d] + 0.5 * R(d),
 'Nasdaq + half rules + pre-FOMC':             lambda d: idx[d] + 0.5 * R(d) + fomc.get(d, 0.0),
 'FULL PACKAGE (+ interest)':                  lambda d: idx[d] + 0.5 * R(d) + fomc.get(d, 0.0) + tb[d],
}
res = {k: stats(f) for k, f in S.items()}
pk, ix = res['FULL PACKAGE (+ interest)'], res['Nasdaq alone']
verdict = 'PASS' if pk['sharpe'] > ix['sharpe'] and pk['worst_drop_pct'] >= ix['worst_drop_pct'] else 'FAIL'
out = dict(era=ERA, note=__doc__, range=[days[0], days[-1]], fomc_days=len(fomc), avg_tbill_pct=round(100 * 252 * sum(tb[d] for d in days) / len(days), 2), results=res, verdict=verdict)
json.dump(out, open(os.path.join(ROOT, 'analysis', f'combo_{ERA}.json'), 'w'), indent=1)
print(json.dumps(out, indent=1, default=str)[:4000])
