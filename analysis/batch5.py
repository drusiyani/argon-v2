"""Analysis only (does not touch the race). Batch 5 (11 Nov 2026): Gemini's T6 proposals, as reviewed by Claude.
Baseline = the FIXED package from batch 4 (VXN-managed core read a day earlier + Argon's rules at half size + pre-FOMC with
the 2011-12 press-conference exit + T-bill interest; roll days use the day's open-to-close).
Pass mark fixed BEFORE the run: a change is ADOPTED only if, in BOTH eras, against the fixed package, it has a higher
per-year return AND a higher Sortino AND a worst drop no more than 1 point deeper AND a bootstrap chance of a drop worse
than -35% no more than 1 point higher. The combination is only considered if both parts pass alone.
  P1 Short gate: short trades of QuantLab / noise band / ATR band are kept only when yesterday's VXN close is at or above
     the 66.7th percentile of all VXN closes from 2009-01-02 up to the day before (expanding); else skipped. Longs and the
     expiry rule unchanged. (Gao et al. 2018 terciles; EdgeLab 2026 short side = volatility-spike bet.)
  P2 Opening-volatility sizing: for QuantLab / noise band / ATR band trades, realised volatility of the 1-minute returns
     from 09:30 up to the entry minute (at most the first 30 minutes) is compared with the same measure over the previous
     252 days: bottom third x0, middle x1, top third x2 (the package's 0.5 rule weight becomes 0 / 0.5 / 1.0).
     The x0/x1/x2 step was chosen by Gemini, not a paper (flagged). Gao et al. 2018 terciles.
  P3 Opening-volume gate: NOT TESTED - Argon's minute data holds prices only, no volume."""
import os, sys, json, math, csv, random, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'engine'))
import portfolio as P
c = P.c
ERA = os.environ.get('ARGON_DATA', 'databento'); risk = P.CONFIG['risk_pct'] / 100; cap = P.CONFIG['cost_cap_R']
LO, HI = (('2021-01-01', '2026-12-31') if ERA == 'databento' else ('2010-07-01', '2020-12-31'))
PC = {'2011-04-27', '2011-06-22', '2011-11-02', '2012-01-25', '2012-04-25', '2012-06-20', '2012-09-13', '2012-12-12'}
def csvmap(fn, col): return {r['date']: float(r[col]) for r in csv.DictReader(open(os.path.join(ROOT, 'analysis', fn)))}
TB = {d: v / 100 / 252 for d, v in csvmap('tbill_dtb3.csv', 'dtb3_pct').items()} if False else None
TB = {r['date']: float(r['dtb3_pct']) / 100 / 252 for r in csv.DictReader(open(os.path.join(ROOT, 'analysis', 'tbill_dtb3.csv')))}

def skipset(S):
    out = {'roll': set(), 'bad': set()}
    for f, k in (('roll', 'roll'), ('bad_days', 'bad')):
        try:
            v = getattr(c, f)(S); v = v.keys() if isinstance(v, dict) else v; out[k] = {x for x in v if isinstance(x, str) and len(x) == 10}
        except Exception: pass
    return out

def lastbefore(src, keys, d):
    import bisect
    i = bisect.bisect_left(keys, d); return (src[keys[i - 1]], i - 1) if i > 0 else (None, -1)

def build(S, volfile, volcol, book_trades):
    D, dl, _ = c.daily(S); T, O, H, L, C, n, mins, days, wd = c.prep(S); sk = skipset(S)
    ret_fix, ret_old = {}, {}
    for k in range(1, len(dl)):
        d, p = dl[k], dl[k - 1]; r = D[d]['c'] / D[p]['c'] - 1
        bad = d in sk['bad'] or p in sk['bad']; roll = d in sk['roll'] or p in sk['roll']
        ret_old[d] = 0.0 if (bad or roll or abs(r) > 0.15) else r
        ret_fix[d] = 0.0 if bad else ((D[d]['c'] / D[d]['o'] - 1) if (roll or abs(r) > 0.15) else r)
    V = csvmap(volfile, volcol); vk = sorted(V); tbk = sorted(TB)
    def volw(d, prev_day):
        v, i = lastbefore(V, vk, prev_day)
        if not v: return 1.0
        h = sorted(V[x] for x in vk[max(0, i - 251):i + 1]); med = h[len(h) // 2] if len(h) >= 60 else v
        return min(1.5, med / v)
    pos = {d: k for k, d in enumerate(dl)}
    w_fix = {dl[k]: volw(dl[k], dl[k - 1]) for k in range(1, len(dl))}            # vol index known before yesterday's close
    w_old = {dl[k]: volw(dl[k], dl[k]) for k in range(1, len(dl))}                # the 11 Nov version (yesterday's close print)
    tb = {d: (lastbefore(TB, tbk, d)[0] or 0.0) for d in dl}
    def fomc(fixed):
        out = {}
        for d in sorted(c.FOMC):
            if d not in pos or pos[d] == 0: continue
            p = dl[pos[d] - 1]
            if d in sk['bad'] or p in sk['bad'] or ((d in sk['roll'] or p in sk['roll']) and not fixed): continue
            lim = 734 if (fixed and d in PC) else 839
            i2 = [i for i in D[d]['r'] if mins[i] <= lim]
            if i2: out[d] = C[i2[-1]] / D[p]['c'] - 1 - c.COST[S] / D[p]['c']
        return out
    f_fix, f_old = fomc(True), fomc(False)
    bk = collections.defaultdict(float); bl = collections.defaultdict(float)
    for t in book_trades:
        x = t.get('w', 1.0) * (t['gross'] - t['cost']); bk[t['date']] += x
        if t['strat'] == 'expiry' or t['side'] in (1, 'long'): bl[t['date']] += x
    return dict(dl=dl, ret_fix=ret_fix, ret_old=ret_old, w_fix=w_fix, w_old=w_old, tb=tb, f_fix=f_fix, f_old=f_old, bk=bk, bl=bl)

def metrics(x):
    eq, peak, dd = 1.0, 1.0, 0.0
    for v in x: eq *= 1 + v; peak = max(peak, eq); dd = min(dd, eq / peak - 1)
    n_ = len(x); m = sum(x) / n_; s = math.sqrt(sum((v - m) ** 2 for v in x) / (n_ - 1)) or 1e-12
    dn = math.sqrt(sum(min(0.0, v) ** 2 for v in x) / n_) or 1e-12
    return dict(final_usd=round(100000 * eq), cagr_pct=round(100 * (max(eq, 1e-9) ** (252 / n_) - 1), 1), sharpe=round(m / s * math.sqrt(252), 2),
                sortino=round(m / dn * math.sqrt(252), 2), worst_drop_pct=round(100 * dd, 1))

def boot(SER, draws=1000, B=63, seed=20261111):
    rng = random.Random(seed); N = len(next(iter(SER.values()))); res = {k: [] for k in SER}
    for _ in range(draws):
        idx = []
        while len(idx) < N: st = rng.randrange(0, N - B); idx.extend(range(st, st + B))
        idx = idx[:N]
        for k, v in SER.items():
            eq, peak, dd = 1.0, 1.0, 0.0
            for i in idx: eq *= 1 + v[i]; peak = max(peak, eq); dd = min(dd, eq / peak - 1)
            res[k].append((max(eq, 1e-9) ** (252 / N) - 1, dd))
    out = {}
    for k, v in res.items():
        cg = sorted(a for a, _ in v); dd = [b for _, b in v]
        out[k] = dict(median_cagr_pct=round(100 * cg[len(cg) // 2], 1), bad_case_cagr_pct_5th=round(100 * cg[len(cg) // 20], 1),
                      chance_losing_money_pct=round(100 * sum(a < 0 for a, _ in v) / draws, 1),
                      chance_drop_worse_than_35_pct=round(100 * sum(b < -.35 for b in dd) / draws, 1))
    return out


VXH = csvmap('vxn.csv', 'vxn'); vxk = sorted(VXH)
def gate_ok(d):
    v, i = lastbefore(VXH, vxk, d)
    if v is None or i < 251: return True
    h = sorted(VXH[x] for x in vxk[:i + 1]); return v >= h[int(len(h) * 2 / 3)]
def rv_table(S):
    D, dl, _ = c.daily(S); T, O, H, L, C, n, mins, days, wd = c.prep(S); out = {}
    for d in dl:
        idx = sorted((i for i in D[d]['r'] if 570 <= mins[i] < 600), key=lambda i: mins[i])
        if not idx or mins[idx[0]] != 570: continue
        cum, acc, prev = [0.0], 0.0, O[idx[0]]
        for i in idx:
            if C[i] > 0 and prev > 0: acc += math.log(C[i] / prev) ** 2
            prev = C[i]; cum.append(math.sqrt(acc))
        out[d] = cum
    return dl, out
BRK = ('quantlab', 'noiseband', 'atrband')
def is_long(t): return t['side'] in (1, 'long') or (isinstance(t['side'], (int, float)) and t['side'] > 0)
def mult_p2(t, dl, RV, pos):
    if t['strat'] not in BRK or t['date'] not in RV or t['date'] not in pos: return 1.0
    K = min(t.get('entry_min', 600), 600) - 570
    if K < 1 or K >= len(RV[t['date']]): return 1.0
    k0 = pos[t['date']]; hist = [RV[x][K] for x in dl[max(0, k0 - 252):k0] if x in RV and K < len(RV[x])]
    if len(hist) < 60: return 1.0
    hist.sort(); a, b = hist[len(hist) // 3], hist[2 * len(hist) // 3]; v = RV[t['date']][K]
    return 0.0 if v <= a else (1.0 if v <= b else 2.0)
trades = P.book(1.0); base = build('NQ', 'vxn.csv', 'vxn', trades)
dl, RV = rv_table('NQ'); pos = {d: k for k, d in enumerate(dl)}
gate = {}
def daily_rules(fn):
    out = collections.defaultdict(float)
    for t in trades: out[t['date']] += fn(t) * t.get('w', 1.0) * (t['gross'] - t['cost'])
    return out
p1 = lambda t: 0.0 if (t['strat'] in BRK and not is_long(t) and not gate.setdefault(t['date'], gate_ok(t['date']))) else 1.0
p2 = lambda t: mult_p2(t, dl, RV, pos)
RULES = {'baseline': daily_rules(lambda t: 1.0), 'P1': daily_rules(p1), 'P2': daily_rules(p2), 'P1+P2': daily_rules(lambda t: p1(t) * p2(t))}
first = min(t['date'] for t in trades); days = [d for d in base['dl'][1:] if max(LO, first) <= d <= HI]
pkg = lambda R: [base['w_fix'][d] * base['ret_fix'][d] + 0.5 * risk * R.get(d, 0.0) + base['f_fix'].get(d, 0.0) + base['tb'][d] for d in days]
SER = {'index alone': [base['ret_fix'][d] for d in days]}
for k, R in RULES.items():
    SER[f'rules {k}'] = [risk * R.get(d, 0.0) for d in days]; SER[f'package {k}'] = pkg(R)
hist = {k: metrics(v) for k, v in SER.items()}; bt = boot(SER)
b0, bb = hist['package baseline'], bt['package baseline']
def ok(k):
    h, b = hist[f'package {k}'], bt[f'package {k}']
    return h['cagr_pct'] > b0['cagr_pct'] and h['sortino'] > b0['sortino'] and h['worst_drop_pct'] >= b0['worst_drop_pct'] - 1 and b['chance_drop_worse_than_35_pct'] <= bb['chance_drop_worse_than_35_pct'] + 1
stats_extra = dict(short_gate_open_share_pct=round(100 * sum(1 for d in days if gate_ok(d)) / len(days), 1),
                   p2_multiplier_counts={str(m): sum(1 for t in trades if days[0] <= t['date'] <= days[-1] and t['strat'] in BRK and p2(t) == m) for m in (0.0, 1.0, 2.0)})
out = dict(era=ERA, note=__doc__, range=[days[0], days[-1]], extra=stats_extra, history=hist, bootstrap=bt,
           verdict_this_era={k: ('PASS' if ok(k) else 'FAIL') for k in ('P1', 'P2', 'P1+P2')})
json.dump(out, open(os.path.join(ROOT, 'analysis', f'batch5_{ERA}.json'), 'w'), indent=1)
print(json.dumps(out['verdict_this_era']), json.dumps(stats_extra))
