"""(batch 3 header below) Second batch, tested exactly as published, on both eras.
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
NOTE = """Analysis only (does not touch the race). Third batch, tested exactly as published, on both eras.
Pass marks fixed BEFORE the run (11 Nov 2026): core changes (H1, H2) PASS if, in BOTH eras, they beat the current best core
(VXN-managed Nasdaq) on Sharpe with a worst drop no deeper. H3 PASSES if mean > 0 and Sharpe >= 0.3 in both eras.
  H1 Halloween (Bouman & Jacobsen 2002): VXN core November-April, cash earning T-bills May-October.
  H2 FOMC cycle (Cieslak, Morse & Vissing-Jorgensen 2019): VXN core at 1.5x in even weeks after a Fed decision, 0.5x in odd weeks.
  H3 Option-expiry week (Stivers & Sun 2013): extra 1x long Saturday-to-third-Friday (the week of monthly expiry), close to close."""
lo, hi = (('2021-01-01', '2026-12-31') if ERA == 'databento' else ('2010-07-01', '2020-12-31'))
lo = max(lo, first)
vxw = {}
vxs = sorted(VX); vi = 0
for d in ld:
    while vi < len(vxs) and vxs[vi] < d: vi += 1
    v = vx_prev[d]
    if not v: vxw[d] = 1.0; continue
    h = sorted(VX[x] for x in vxs[max(0, vi - 252):vi]); med = h[len(h) // 2] if len(h) >= 60 else v
    vxw[d] = min(1.5, med / v)
core = lambda d, m=1.0: m * vxw[d] * ret[d] + (1 - m * vxw[d]) * (tb_prev[d] or 0.0)
# H2: FOMC cycle week, counted in trading days from the day before the latest decision (that day = 0)
fd = sorted(x for x in c.FOMC if x in pos); cyc = {}
for k, d in enumerate(ld):
    prior = [x for x in fd if x <= d]
    if not prior: continue
    p0 = pos[prior[-1]] - 1; cyc[d] = ((pos[d] - p0) // 5) % 2 == 0
# H3: option-expiry week = the trading days after the Friday before the third Friday, up to and including the third Friday
def third_friday(y, m):
    d0 = dt.date(y, m, 1); return d0 + dt.timedelta(days=(4 - d0.weekday()) % 7 + 14)
opx = set()
for d in ld:
    a_ = dt.date.fromisoformat(d); tf = third_friday(a_.year, a_.month)
    if tf - dt.timedelta(days=6) <= a_ <= tf: opx.add(d)
days_e = [d for d in ld if lo <= d <= hi]
def stats(f):
    eq, peak, dd, xs = 1.0, 1.0, 0.0, []
    for d in days_e:
        r = f(d); xs.append(r); eq *= 1 + r; peak = max(peak, eq); dd = min(dd, eq / peak - 1)
    m = sum(xs) / len(xs); s = math.sqrt(sum((v - m) ** 2 for v in xs) / (len(xs) - 1)) or 1
    return dict(final_usd=round(100000 * eq), cagr_pct=round(100 * (eq ** (252 / len(xs)) - 1), 1), sharpe=round(m / s * math.sqrt(252), 2), worst_drop_pct=round(100 * dd, 1))
R = lambda d: risk * book.get(d, 0.0); tbd = lambda d: tb_prev[d] or 0.0
halloween = lambda d: core(d) if int(d[5:7]) in (11, 12, 1, 2, 3, 4) else tbd(d)
fomcc = lambda d: core(d, 1.5 if cyc.get(d, True) else 0.5)
h3 = lambda d: (ret[d] - (COST / D[d]['c'] if dt.date.fromisoformat(d).weekday() == 4 else 0.0)) if d in opx else 0.0
res = {'Nasdaq alone': stats(lambda d: ret[d]), 'VXN core (current best)': stats(core),
       'H1 VXN core + Halloween': stats(halloween), 'H2 VXN core + FOMC cycle': stats(fomcc), 'H3 option-expiry week (alone)': stats(h3)}
b = res['VXN core (current best)']
ok = lambda k: res[k]['sharpe'] > b['sharpe'] and res[k]['worst_drop_pct'] >= b['worst_drop_pct']
verdict = {'H1 VXN core + Halloween': ok('H1 VXN core + Halloween'), 'H2 VXN core + FOMC cycle': ok('H2 VXN core + FOMC cycle'),
           'H3 option-expiry week (alone)': res['H3 option-expiry week (alone)']['final_usd'] > 100000 and res['H3 option-expiry week (alone)']['sharpe'] >= 0.3}
base_pkg = lambda d, cf=core: cf(d) + 0.5 * R(d) + fomc.get(d, 0.0) + tbd(d)
res['BEST PACKAGE (VXN core + half rules + pre-FOMC + interest)'] = stats(base_pkg)
res['best package with H1'] = stats(lambda d: base_pkg(d, halloween))
res['best package with H2'] = stats(lambda d: base_pkg(d, fomcc))
res['best package + H3'] = stats(lambda d: base_pkg(d) + h3(d))
out = dict(era=ERA, note=NOTE, range=[days_e[0], days_e[-1]], verdict_this_era={k: 'PASS' if v else 'FAIL' for k, v in verdict.items()}, results=res)
json.dump(out, open(os.path.join(ROOT, 'analysis', f'edges3_{ERA}.json'), 'w'), indent=1)
print(json.dumps(out['verdict_this_era'], indent=1)); [print(k, v) for k, v in res.items()]
