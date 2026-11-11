"""Analysis only (does not touch the race). Every researched change, tested on BOTH eras. Pass marks fixed before the run (11 Nov 2026):
  T1 Index + rules at half size: PASS if Sharpe beats the index alone AND worst drop no deeper than the index alone.
  T2 Interest on idle cash (3-month T-bill, FRED DTB3): accounting, no pass mark; reported so its size is visible.
  T3 Hedge weighting of QuantLab / noise-band variants (exponential weights, anytime learning rate, no tuning)
     instead of the monthly best-variant re-pick: PASS if Sharpe >= today's + 0.15 AND worst drop no deeper.
  T4 Risk-parity weights across the four rules (1/stdev of each rule's last 6 months, average weight 1, as the shadow book):
     same pass mark as T3.
  A change is only recommended if it passes in BOTH eras. Daily compounding at 1% risk per 1R.
Run once per era: default (2021-26, built on) and ARGON_DATA=lockbox2010 (2011-20, sealed era, already opened once)."""
import os, sys, json, math, csv, io, urllib.request, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'engine'))
import portfolio as P
c = P.c
ERA = os.environ.get('ARGON_DATA', 'databento'); risk = P.CONFIG['risk_pct'] / 100; cap = P.CONFIG['cost_cap_R']
R = P.raw()
def keep(ts): return [t for t in ts if t['cost'] <= cap]
def net(t): return t.get('w', 1.0) * (t['gross'] - t['cost'])

def hedge(trades, look=6):
    """Exponential weights over variants. Month i uses only months before i; first `look` months skipped, like the re-pick."""
    if not trades: return []
    mon = collections.defaultdict(lambda: collections.defaultdict(float)); ml = collections.defaultdict(lambda: collections.defaultdict(list))
    for t in trades: mon[t['variant']][t['month']] += t['gross'] - t['cost']; ml[t['variant']][t['month']].append(t)
    vs = sorted(mon); months = sorted({t['month'] for t in trades}); N = len(vs); out = []
    for i, m in enumerate(months[look:], look):
        past = months[:i]; B = max(abs(mon[v][p]) for v in vs for p in past) or 1.0
        eta = math.sqrt(8 * math.log(max(N, 2)) / i)
        s = {v: sum(mon[v][p] for p in past) / B for v in vs}; top = max(s.values())
        w = {v: math.exp(eta / 2 * (s[v] - top)) for v in vs}; z = sum(w.values())
        for v in vs: out += [dict(t, w=w[v] / z) for t in ml[v][m]]
    return out

def parity(trades, look=6):
    gm = collections.defaultdict(lambda: collections.defaultdict(float))
    for t in trades: gm[t['strat']][t['month']] += net(t)
    allm = c.months_between(min(t['month'] for t in trades), max(t['month'] for t in trades)); W = {}
    for i, m in enumerate(allm):
        prev = allm[max(0, i - look):i]
        if len(prev) < look: continue
        sd = {g: math.sqrt(sum((gm[g].get(p, 0) - sum(gm[g].get(q, 0) for q in prev) / look) ** 2 for p in prev) / look) for g in P.GROUPS}
        inv = {g: 1 / sd[g] for g in P.GROUPS if sd[g] > 0}
        if not inv: continue
        mu = sum(inv.values()) / len(inv); W[m] = {g: inv.get(g, mu) / mu for g in P.GROUPS}
    return [dict(t, w=t.get('w', 1.0) * W.get(t['month'], {}).get(t['strat'], 1.0)) for t in trades]

base = keep([dict(t, w=1.0) for t in c.walkforward(R['quantlab'])] + [dict(t, w=1.0) for t in c.walkforward(R['noiseband'])] +
            [dict(t, w=1.0) for t in R['atrband']] + [dict(t, w=1.0) for t in R['expiry']])
hed = keep(hedge(R['quantlab']) + hedge(R['noiseband']) + [dict(t, w=1.0) for t in R['atrband']] + [dict(t, w=1.0) for t in R['expiry']])
BOOKS = {'today': base, 'T3 hedge': hed, 'T4 parity': parity(base), 'T3+T4': parity(hed)}
daily = {k: collections.defaultdict(float) for k in BOOKS}
for k, ts in BOOKS.items():
    for t in ts: daily[k][t['date']] += net(t)

D, dl, _ = c.daily('NQ'); skip = set()
for f in ('roll', 'bad_days'):
    try:
        v = getattr(c, f)('NQ'); v = v.keys() if isinstance(v, dict) else v; skip |= {x for x in v if isinstance(x, str) and len(x) == 10}
    except Exception: pass
idx = {}
for k in range(1, len(dl)):
    d, p = dl[k], dl[k - 1]; r = D[d]['c'] / D[p]['c'] - 1
    idx[d] = 0.0 if (d in skip or p in skip or abs(r) > 0.15) else r
try:
    raw = urllib.request.urlopen(urllib.request.Request('https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTB3', headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read().decode()
    TB = {r['observation_date']: float(r['DTB3']) / 100 / 252 for r in csv.DictReader(io.StringIO(raw)) if r['DTB3'] not in ('.', '')}
except Exception as ex: print('T-bill fetch failed:', ex); TB = {}
tbd = sorted(TB); last = 0.0; tb = {}
j = 0
for d in sorted(idx):
    while j < len(tbd) and tbd[j] <= d: last = TB[tbd[j]]; j += 1
    tb[d] = last
start = max(min(t['date'] for t in base if t['month'] >= min(t2['month'] for t2 in hed)), min(idx))
days = [d for d in sorted(idx) if d >= start]

def stats(rets):
    eq, peak, dd, yr = 1.0, 1.0, 0.0, collections.OrderedDict()
    for d, r in rets: yr.setdefault(d[:4], eq); eq *= 1 + r; peak = max(peak, eq); dd = min(dd, eq / peak - 1)
    x = [r for _, r in rets]; m = sum(x) / len(x); s = math.sqrt(sum((v - m) ** 2 for v in x) / (len(x) - 1)); ys = list(yr)
    return dict(final_usd=round(100000 * eq), cagr_pct=round(100 * (eq ** (252 / len(x)) - 1), 1), sharpe=round(m / s * math.sqrt(252), 2), worst_drop_pct=round(100 * dd, 1),
                years={y: round(100 * ((yr[ys[i + 1]] if i + 1 < len(ys) else eq) / yr[y] - 1), 1) for i, y in enumerate(ys)})
S = {
 'today (rules alone)':            [(d, risk * daily['today'].get(d, 0)) for d in days],
 'T2 today + interest':            [(d, risk * daily['today'].get(d, 0) + tb[d]) for d in days],
 'T3 hedge weighting':             [(d, risk * daily['T3 hedge'].get(d, 0)) for d in days],
 'T4 risk parity':                 [(d, risk * daily['T4 parity'].get(d, 0)) for d in days],
 'T3+T4':                          [(d, risk * daily['T3+T4'].get(d, 0)) for d in days],
 'index alone':                    [(d, idx[d]) for d in days],
 'index alone + interest':         [(d, idx[d] + tb[d]) for d in days],
 'T1 index + half rules':          [(d, idx[d] + 0.5 * risk * daily['today'].get(d, 0)) for d in days],
 'PACKAGE index + half rules + interest': [(d, idx[d] + 0.5 * risk * daily['today'].get(d, 0) + tb[d]) for d in days],
 'PACKAGE + T3+T4':                [(d, idx[d] + 0.5 * risk * daily['T3+T4'].get(d, 0) + tb[d]) for d in days],
}
res = {k: stats(v) for k, v in S.items()}
b, ix = res['today (rules alone)'], res['index alone']
ok = lambda k: res[k]['sharpe'] >= b['sharpe'] + 0.15 and res[k]['worst_drop_pct'] >= b['worst_drop_pct']
verdict = {'T1 index + half rules': 'PASS' if res['T1 index + half rules']['sharpe'] > ix['sharpe'] and res['T1 index + half rules']['worst_drop_pct'] >= ix['worst_drop_pct'] else 'FAIL',
           'T3 hedge weighting': 'PASS' if ok('T3 hedge weighting') else 'FAIL', 'T4 risk parity': 'PASS' if ok('T4 risk parity') else 'FAIL', 'T3+T4': 'PASS' if ok('T3+T4') else 'FAIL'}
out = dict(era=ERA, note=__doc__, range=[days[0], days[-1]], days=len(days), tbill_loaded=bool(TB), results=res, verdict=verdict)
fn = os.path.join(ROOT, 'analysis', f'tests_{ERA}.json'); json.dump(out, open(fn, 'w'), indent=1)
print(json.dumps(dict(era=ERA, verdict=verdict, results={k: {x: v[x] for x in ('final_usd', 'cagr_pct', 'sharpe', 'worst_drop_pct')} for k, v in res.items()}), indent=1))
