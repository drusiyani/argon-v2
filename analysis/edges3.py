"""Analysis only (does not touch the race). THIRD batch (core timing), tested exactly as published, on both eras.
Pass mark fixed BEFORE the run (11 Nov 2026): PASS if, in BOTH eras, Sharpe beats holding the Nasdaq AND the worst drop is shallower.
  H1 FOMC cycle (Cieslak, Morse & Vissing-Jorgensen 2019): hold 1x Nasdaq only in even weeks of the FOMC cycle
     (trading days -1..3, 9..13, 19..23, 29..33 around the last scheduled decision), else T-bills.
  H2 Halloween (Bouman & Jacobsen 2002): hold 1x Nasdaq November to April, T-bills May to October.
  H3 VIX term structure: hold 1x Nasdaq when yesterday's VIX / 3-month VIX < 1 (normal), else T-bills.
Each is also tried on top of the VXN-managed core inside the current package. Old docstring follows.
Second batch, tested exactly as published, on both eras.
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

VIX = {r['date']: float(r['vixcls']) for r in csv.DictReader(open(os.path.join(ROOT, 'analysis', 'VIXCLS.csv')))}
VX3 = {r['date']: float(r['vxvcls']) for r in csv.DictReader(open(os.path.join(ROOT, 'analysis', 'VXVCLS.csv')))}
vix_p, vx3_p = carry(VIX), carry(VX3)
fl = sorted(d for d in c.FOMC)
lpos = {d: k for k, d in enumerate(ld)}
def cycle_day(k):
    d = ld[k]
    nxt = [f for f in fl if f >= d]
    if nxt and nxt[0] in lpos and lpos[nxt[0]] - k == 1: return -1
    prv = [f for f in fl if f <= d and f in lpos]
    return k - lpos[prv[-1]] if prv else None
EVEN = set(range(0, 4)) | set(range(9, 14)) | set(range(19, 24)) | set(range(29, 34))
vxw = {}
for k, d in enumerate(ld):
    v = vx_prev[d]
    if v:
        i = sum(1 for x in vxh if x < d); h = sorted(VX[x] for x in vxh[max(0, i - 252):i])
        vxw[d] = min(1.5, (h[len(h) // 2] if len(h) >= 60 else v) / v)
    else: vxw[d] = 1.0
on = {'H1 FOMC even weeks': {}, 'H2 Halloween (Nov-Apr)': {}, 'H3 VIX term structure': {}}
for k, d in enumerate(ld):
    cd = cycle_day(k)
    on['H1 FOMC even weeks'][d] = cd is not None and (cd == -1 or cd in EVEN)
    on['H2 Halloween (Nov-Apr)'][d] = int(d[5:7]) in (11, 12, 1, 2, 3, 4)
    a, b = vix_p[d], vx3_p[d]
    on['H3 VIX term structure'][d] = not (a and b and a / b >= 1)
def timed(name, w=lambda d: 1.0):
    flag = on[name]; prev = [None]
    def f(d):
        x = w(d) * ret[d] + (1 - w(d)) * (tb_prev[d] or 0.0) if flag[d] else (tb_prev[d] or 0.0)
        if prev[0] is not None and flag[d] != prev[0]: x -= COST / D[d]['c']
        prev[0] = flag[d]; return x
    return f
days_e = [d for d in ld if lo <= d <= hi]
def stats(f):
    eq, peak, dd, xs = 1.0, 1.0, 0.0, []
    for d in days_e:
        r = f(d); xs.append(r); eq *= 1 + r; peak = max(peak, eq); dd = min(dd, eq / peak - 1)
    m = sum(xs) / len(xs); s = math.sqrt(sum((v - m) ** 2 for v in xs) / (len(xs) - 1)) or 1
    return dict(final_usd=round(100000 * eq), cagr_pct=round(100 * (eq ** (252 / len(xs)) - 1), 1), sharpe=round(m / s * math.sqrt(252), 2), worst_drop_pct=round(100 * dd, 1))
R = lambda d: risk * book.get(d, 0.0); tbd = lambda d: tb_prev[d] or 0.0
vcore = lambda d: vxw[d] * ret[d] + (1 - vxw[d]) * tbd(d)
res = {'Nasdaq alone': stats(lambda d: ret[d]), 'VXN core (batch 2 pass)': stats(vcore)}
for nm in on: res[nm] = stats(timed(nm))
ix = res['Nasdaq alone']
verdict = {nm: 'PASS' if res[nm]['sharpe'] > ix['sharpe'] and res[nm]['worst_drop_pct'] > ix['worst_drop_pct'] else 'FAIL' for nm in on}
res['PACKAGE: VXN core + half rules + pre-FOMC + interest'] = stats(lambda d: vcore(d) + 0.5 * R(d) + fomc.get(d, 0.0))
for nm in on:
    g = timed(nm, lambda d: vxw[d])
    res[f'PACKAGE with {nm} on the VXN core'] = stats(lambda d, g=g: g(d) + 0.5 * R(d) + fomc.get(d, 0.0))
out = dict(era=ERA, note=__doc__, range=[days_e[0], days_e[-1]], verdict_this_era=verdict, results=res)
json.dump(out, open(os.path.join(ROOT, 'analysis', f'edges3_{ERA}.json'), 'w'), indent=1)
print(json.dumps(verdict)); [print(k, v) for k, v in res.items()]
