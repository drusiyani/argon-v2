"""Analysis only (does not touch the race). Two ideas, pass marks fixed BEFORE the run (11 Nov 2026):

A. Gamma filter: size each day by the PREVIOUS day's dealer gamma (SqueezeMetrics GEX, free history).
   A1: full size if prior-day GEX < 0 (dealers short gamma), half size otherwise.
   A2: full size if prior-day GEX is below its trailing 252-day median, half size otherwise.
   PASS if Sharpe beats the plain rules by >= 0.15 AND the worst drawdown is no deeper, over 2021-26.
B. Index + rules: hold 1x Nasdaq futures every day, plus the rules at half size.
   PASS if Sharpe beats the index alone AND the worst drawdown is no deeper than the index alone.
Era: 2021-07 to now only (the daily Nasdaq series this loader has starts 2021). In-sample, so a pass is weak evidence.
Daily compounding, so figures differ slightly from the official monthly book."""
import os, sys, json, math, csv, io, urllib.request, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'engine'))
import portfolio as P
c = P.c
tr = P.book(1.0); risk = P.CONFIG['risk_pct'] / 100
net = lambda t: t['w'] * (t['gross'] - t['cost'])
book = collections.defaultdict(float)
for t in tr: book[t['date']] += net(t)
D, dl, _ = c.daily('NQ')
skip = set()
for f in ('roll', 'bad_days'):
    try:
        v = getattr(c, f)('NQ'); v = v.keys() if isinstance(v, dict) else v
        skip |= {x for x in v if isinstance(x, str) and len(x) == 10}
    except Exception: pass
idx = {}
for k in range(1, len(dl)):
    d, p = dl[k], dl[k - 1]
    r = D[d]['c'] / D[p]['c'] - 1
    idx[d] = 0.0 if (d in skip or p in skip or abs(r) > 0.15) else r
raw = urllib.request.urlopen(urllib.request.Request('https://squeezemetrics.com/monitor/static/DIX.csv', headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read().decode()
G = {r['date']: float(r['gex']) for r in csv.DictReader(io.StringIO(raw))}
gd = sorted(G)
prev = {}                                    # day -> GEX published at the close of the previous trading day
for k in range(1, len(gd)): prev[gd[k]] = (G[gd[k - 1]], [G[x] for x in gd[max(0, k - 253):k - 1]])
start = max(min(t['date'] for t in tr), min(idx))
days = [d for d in sorted(idx) if d >= start and d in prev]

def a1(d): return 1.0 if prev[d][0] < 0 else 0.5
def a2(d):
    h = sorted(prev[d][1]); return 1.0 if len(h) < 60 or prev[d][0] < h[len(h) // 2] else 0.5

def stats(rets):
    eq, peak, dd, yr = 1.0, 1.0, 0.0, collections.OrderedDict()
    for d, r in rets:
        y = d[:4]; yr.setdefault(y, eq); eq *= 1 + r; peak = max(peak, eq); dd = min(dd, eq / peak - 1)
    x = [r for _, r in rets]; m = sum(x) / len(x); s = math.sqrt(sum((v - m) ** 2 for v in x) / (len(x) - 1))
    yrs = len(x) / 252; ys = list(yr)
    by = {y: round(100 * ((yr[ys[i + 1]] if i + 1 < len(ys) else eq) / yr[y] - 1), 1) for i, y in enumerate(ys)}
    return dict(final_usd=round(100000 * eq), cagr_pct=round(100 * (eq ** (1 / yrs) - 1), 1), sharpe=round(m / s * math.sqrt(252), 2),
                worst_drop_pct=round(100 * dd, 1), years=by)

S = {
 'rules (today, 1% risk)':           [(d, risk * book.get(d, 0)) for d in days],
 'A1 rules + gamma sign filter':     [(d, risk * book.get(d, 0) * a1(d)) for d in days],
 'A2 rules + gamma median filter':   [(d, risk * book.get(d, 0) * a2(d)) for d in days],
 'index alone (1x Nasdaq)':          [(d, idx[d]) for d in days],
 'B index + rules at half size':     [(d, idx[d] + 0.5 * risk * book.get(d, 0)) for d in days],
 'B+A2 index + half rules, gamma':   [(d, idx[d] + 0.5 * risk * book.get(d, 0) * a2(d)) for d in days],
}
res = {k: stats(v) for k, v in S.items()}
neg = [book.get(d, 0) for d in days if prev[d][0] < 0]; pos = [book.get(d, 0) for d in days if prev[d][0] >= 0]
lo = [book.get(d, 0) for d in days if a2(d) == 1.0]; hi = [book.get(d, 0) for d in days if a2(d) == 0.5]
diag = dict(short_gamma_days=len(neg), book_avg_R_short_gamma=round(sum(neg) / len(neg), 3), long_gamma_days=len(pos), book_avg_R_long_gamma=round(sum(pos) / len(pos), 3),
            below_median_days=len(lo), book_avg_R_below_median=round(sum(lo) / len(lo), 3), above_median_days=len(hi), book_avg_R_above_median=round(sum(hi) / len(hi), 3))
base, ix = res['rules (today, 1% risk)'], res['index alone (1x Nasdaq)']
verdict = {k: ('PASS' if res[k]['sharpe'] >= base['sharpe'] + 0.15 and res[k]['worst_drop_pct'] >= base['worst_drop_pct'] else 'FAIL') for k in ('A1 rules + gamma sign filter', 'A2 rules + gamma median filter')}
verdict['B index + rules at half size'] = 'PASS' if res['B index + rules at half size']['sharpe'] > ix['sharpe'] and res['B index + rules at half size']['worst_drop_pct'] >= ix['worst_drop_pct'] else 'FAIL'
out = dict(note=__doc__, range=[days[0], days[-1]], days=len(days), diagnostics=diag, results=res, verdict=verdict)
json.dump(out, open(os.path.join(ROOT, 'analysis', 'both.json'), 'w'), indent=1)
print(json.dumps(dict(diagnostics=diag, results=res, verdict=verdict), indent=1))
