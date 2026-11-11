"""Analysis only (does not touch the race). Second batch, tested exactly as published, on both eras.
Pass marks fixed BEFORE the run (11 Nov 2026):
  Core changes (G1, G2) PASS if, in BOTH eras, Sharpe beats holding the Nasdaq AND the worst drop is shallower.
  Timing edges (G3, G4) PASS if, in BOTH eras, mean > 0 AND Sharpe >= 0.3.
  G1 200-day trend filter (Faber): hold 1x Nasdaq while yesterday's close > its 200-day average, else cash earning T-bills.
  G2 VXN-managed core: exposure = trailing-252-day median VXN / yesterday's VXN, capped at 1.5 (no fitted constant).
  G3 Buy the dip (Connors RSI-2): long at the close when RSI(2) < 10 and close > 200-day average; out at the first close
     above the 5-day average.
  G4 Pre-holiday: long over the last trading day before a weekday market holiday (close to close).
Prices: a roll-free Nasdaq level built from the futures' daily returns (roll days count as 0). Costs 0.75 NQ pts per round
trip. If any pass, the package (Nasdaq core + half rules + pre-FOMC + interest) is re-run with them."""
import os, sys, json, math, csv, collections, datetime as dt
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
ret = {dl[k]: (0.0 if (dl[k] in skip or dl[k - 1] in skip or abs(D[dl[k]]['c'] / D[dl[k - 1]]['c'] - 1) > 0.15) else D[dl[k]]['c'] / D[dl[k - 1]]['c'] - 1) for k in range(1, len(dl))}
lvl = {}; x = 100.0
for d in dl[1:]: x *= 1 + ret[d]; lvl[d] = x
ld = dl[1:]
def sma(k, w): return sum(lvl[ld[j]] for j in range(k - w + 1, k + 1)) / w if k >= w - 1 else None
def rsi2(k):
    if k < 3: return None
    up = [max(0, lvl[ld[j]] - lvl[ld[j - 1]]) for j in (k - 1, k)]; dn = [max(0, lvl[ld[j - 1]] - lvl[ld[j]]) for j in (k - 1, k)]
    a, b = sum(up) / 2, sum(dn) / 2
    return 100.0 if b == 0 else 100 - 100 / (1 + a / b)
TB = {r['date']: float(r['dtb3_pct']) / 100 / 252 for r in csv.DictReader(open(os.path.join(ROOT, 'analysis', 'tbill_dtb3.csv')))}
VX = {r['date']: float(r['vxn']) for r in csv.DictReader(open(os.path.join(ROOT, 'analysis', 'vxn.csv')))}
def carry(src):
    ks = sorted(src); out = {}; j = 0; last = None
    for d in ld:
        while j < len(ks) and ks[j] < d: last = src[ks[j]]; j += 1     # strictly before d: yesterday's value
        out[d] = last
    return out
tb_prev = carry(TB); vx_prev = carry(VX); vxh = sorted(VX)
book = collections.defaultdict(float); first = None
for t in P.book(1.0): book[t['date']] += t['w'] * (t['gross'] - t['cost']); first = min(first or t['date'], t['date'])
fomc = {}; pos = {d: k for k, d in enumerate(dl)}
for d in sorted(c.FOMC):
    if d not in pos or pos[d] == 0: continue
    p = dl[pos[d] - 1]
    if d in skip or p in skip: continue
    i2 = [i for i in D[d]['r'] if mins[i] <= 839]
    if i2: fomc[d] = C[i2[-1]] / D[p]['c'] - 1 - COST / D[p]['c']
lo, hi = (('2021-01-01', '2026-12-31') if ERA == 'databento' else ('2010-07-01', '2020-12-31'))
lo = max(lo, first)
g1, g2, g3, g4 = {}, {}, {}, {}
inpos = False; prev_in1 = None
for k, d in enumerate(ld):
    if k == 0: continue
    s200 = sma(k - 1, 200)
    on1 = s200 is not None and lvl[ld[k - 1]] > s200
    g1[d] = ret[d] if on1 else (tb_prev[d] or 0.0)
    if prev_in1 is not None and on1 != prev_in1: g1[d] -= COST / (D[d]['c'] or 1)
    prev_in1 = on1
    v = vx_prev[d]
    if v:
        i = sum(1 for x in vxh if x < d); h = sorted(VX[x] for x in vxh[max(0, i - 252):i])
        med = h[len(h) // 2] if len(h) >= 60 else v
        w = min(1.5, med / v)
    else: w = 1.0
    g2[d] = w * ret[d] + (1 - w) * (tb_prev[d] or 0.0)
    if inpos:
        g3[d] = ret[d]
        if lvl[d] > sma(k, 5): inpos = False; g3[d] -= COST / D[d]['c']
    if not inpos:
        r2, s = rsi2(k), sma(k, 200)
        if r2 is not None and s is not None and r2 < 10 and lvl[d] > s: inpos = True
for k in range(1, len(ld) - 1):
    d, nx = ld[k], ld[k + 1]
    a, b = dt.date.fromisoformat(d), dt.date.fromisoformat(nx)
    gap = [a + dt.timedelta(days=j) for j in range(1, (b - a).days)]
    if any(x.weekday() < 5 for x in gap): g4[d] = ret[d] - COST / D[d]['c']
days_e = [d for d in ld if lo <= d <= hi]
def stats(f, timing=False):
    eq, peak, dd, xs = 1.0, 1.0, 0.0, []
    for d in days_e:
        r = f(d); xs.append(r); eq *= 1 + r; peak = max(peak, eq); dd = min(dd, eq / peak - 1)
    m = sum(xs) / len(xs); s = math.sqrt(sum((v - m) ** 2 for v in xs) / (len(xs) - 1)) or 1
    return dict(final_usd=round(100000 * eq), cagr_pct=round(100 * (eq ** (252 / len(xs)) - 1), 1), sharpe=round(m / s * math.sqrt(252), 2),
                worst_drop_pct=round(100 * dd, 1), days_in=sum(1 for v in xs if v != 0) if timing else None)
R = lambda d: risk * book.get(d, 0.0); tbd = lambda d: tb_prev[d] or 0.0
res = {'Nasdaq alone': stats(lambda d: ret[d]), 'G1 200-day trend filter': stats(lambda d: g1.get(d, 0.0)),
       'G2 VXN-managed core': stats(lambda d: g2.get(d, ret[d])), 'G3 buy the dip (RSI-2)': stats(lambda d: g3.get(d, 0.0), True),
       'G4 pre-holiday': stats(lambda d: g4.get(d, 0.0), True)}
ix = res['Nasdaq alone']
core_ok = lambda k: res[k]['sharpe'] > ix['sharpe'] and res[k]['worst_drop_pct'] > ix['worst_drop_pct']
time_ok = lambda k: res[k]['final_usd'] > 100000 and res[k]['sharpe'] >= 0.3
verdict = {'G1 200-day trend filter': core_ok('G1 200-day trend filter'), 'G2 VXN-managed core': core_ok('G2 VXN-managed core'),
           'G3 buy the dip (RSI-2)': time_ok('G3 buy the dip (RSI-2)'), 'G4 pre-holiday': time_ok('G4 pre-holiday')}
pkg = {'package (Nasdaq + half rules + pre-FOMC + interest)': lambda d: ret[d] + 0.5 * R(d) + fomc.get(d, 0.0) + tbd(d),
       'package with G1 core': lambda d: g1.get(d, 0.0) + 0.5 * R(d) + fomc.get(d, 0.0) + tbd(d),
       'package with G2 core': lambda d: g2.get(d, ret[d]) + 0.5 * R(d) + fomc.get(d, 0.0) + tbd(d),
       'package + G3': lambda d: ret[d] + 0.5 * R(d) + fomc.get(d, 0.0) + tbd(d) + g3.get(d, 0.0),
       'package + G4': lambda d: ret[d] + 0.5 * R(d) + fomc.get(d, 0.0) + tbd(d) + g4.get(d, 0.0)}
for k, f in pkg.items(): res[k] = stats(f)
out = dict(era=ERA, note=__doc__, range=[days_e[0], days_e[-1]], verdict_this_era={k: 'PASS' if v else 'FAIL' for k, v in verdict.items()}, results=res)
json.dump(out, open(os.path.join(ROOT, 'analysis', f'edges2_{ERA}.json'), 'w'), indent=1)
print(json.dumps(out['verdict_this_era'], indent=1)); [print(k, v) for k, v in res.items()]
