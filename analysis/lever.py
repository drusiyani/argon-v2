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
NOTE = """Analysis only (does not touch the race). Leverage on the best package, with Sortino ratios and a paired block bootstrap.
Pass mark fixed BEFORE the run (11 Nov 2026): a leverage level PASSES if, in BOTH eras, the historical worst drop is shallower
than -35% AND under 20% of bootstrapped histories have a worst drop deeper than -35%.
Package = VXN-managed Nasdaq core + Argon rules at half size + pre-FOMC tilt; leverage k scales those, T-bill interest on cash
is added once. Bootstrap: 1,000 resamples of each era, 21-trading-day blocks (about a month, keeps volatility clustering),
the SAME blocks for every strategy so their comparison is paired. Seed 20261111."""
import random
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
days_e = [d for d in ld if lo <= d <= hi]
R = lambda d: risk * book.get(d, 0.0); tbd = lambda d: tb_prev[d] or 0.0
risky = lambda d: core(d) - (1 - vxw[d]) * tbd(d) + 0.5 * R(d) + fomc.get(d, 0.0)     # core's own cash leg removed; interest added once below
SER = {'Nasdaq alone': [ret[d] for d in days_e],
       'existing rules alone': [R(d) for d in days_e],
       '"$2.28m" rules + pre-FOMC + interest': [R(d) + fomc.get(d, 0.0) + tbd(d) for d in days_e]}
for k in (1.0, 1.25, 1.5): SER[f'package {k}x'] = [k * risky(d) + tbd(d) for d in days_e]
def metrics(x):
    eq, peak, dd = 1.0, 1.0, 0.0
    for v in x: eq *= 1 + v; peak = max(peak, eq); dd = min(dd, eq / peak - 1)
    n_ = len(x); m = sum(x) / n_; s = math.sqrt(sum((v - m) ** 2 for v in x) / (n_ - 1)) or 1e-12
    dn = math.sqrt(sum(min(0.0, v) ** 2 for v in x) / n_) or 1e-12
    return dict(final_usd=round(100000 * eq), cagr_pct=round(100 * (max(eq, 1e-9) ** (252 / n_) - 1), 1), sharpe=round(m / s * math.sqrt(252), 2),
                sortino=round(m / dn * math.sqrt(252), 2), worst_drop_pct=round(100 * dd, 1))
hist = {k: metrics(v) for k, v in SER.items()}
rng = random.Random(20261111); N = len(days_e); B = 21; draws = 1000; boot = {k: [] for k in SER}
for _ in range(draws):
    idxs = []
    while len(idxs) < N:
        st = rng.randrange(0, N - B); idxs.extend(range(st, st + B))
    idxs = idxs[:N]
    for k, v in SER.items():
        eq, peak, dd = 1.0, 1.0, 0.0
        for i in idxs: eq *= 1 + v[i]; peak = max(peak, eq); dd = min(dd, eq / peak - 1)
        boot[k].append((max(eq, 1e-9) ** (252 / N) - 1, dd))
def pct(a, p): a = sorted(a); return a[min(len(a) - 1, int(p * len(a)))]
bres = {}
for k, v in boot.items():
    cg = [c for c, _ in v]; dd = [d for _, d in v]; ix = [c for c, _ in boot['Nasdaq alone']]
    bres[k] = dict(median_cagr_pct=round(100 * pct(cg, .5), 1), bad_case_cagr_pct_5th=round(100 * pct(cg, .05), 1), good_case_cagr_pct_95th=round(100 * pct(cg, .95), 1),
                   chance_of_losing_money_pct=round(100 * sum(c < 0 for c in cg) / draws, 1), typical_worst_drop_pct=round(100 * pct(dd, .5), 1),
                   bad_case_worst_drop_pct_5th=round(100 * pct(dd, .05), 1), chance_drop_worse_than_35_pct=round(100 * sum(d < -.35 for d in dd) / draws, 1),
                   chance_beats_nasdaq_pct=round(100 * sum(a > b for a, b in zip(cg, ix)) / draws, 1))
verdict = {k: ('PASS' if hist[k]['worst_drop_pct'] > -35 and bres[k]['chance_drop_worse_than_35_pct'] < 20 else 'FAIL') for k in SER if k.startswith('package')}
out = dict(era=ERA, note=NOTE, range=[days_e[0], days_e[-1]], verdict_this_era=verdict, history=hist, bootstrap=bres)
json.dump(out, open(os.path.join(ROOT, 'analysis', f'lever_{ERA}.json'), 'w'), indent=1)
print(json.dumps(out['verdict_this_era'], indent=1)); [print(k, hist[k], bres[k]) for k in SER]
