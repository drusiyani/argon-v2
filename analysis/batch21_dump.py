"""Batch 21 step 1 (run once per era): the QuantLab hold leg's daily returns (Nasdaq and S&P) and the cost-rule diagnostic.
Saved to analysis/_cache/ for batch21.py. See BATCH21_PREREG.md."""

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




kw = P.CONFIG['strategies']; raw = P.raw()
def leg(sym, rawq):
    T, O, H, L, C, n, mins, cdays, wd = c.prep(sym); D, dl, atr = c.daily(sym); sig = {}; out = {}
    for t in rawq: sig.setdefault(t['date'], t)                      # one signal per day (every variant shares side and entry)
    for d, t in sig.items():
        if not (LO <= d <= HI) or d not in D or t['entry_min'] != 575: continue
        r = [i for i in D[d]['r'] if mins[i] <= 954]
        if not r or mins[r[-1]] < 900: continue                      # half days: no 15:54 bar
        s = 1 if t['side'] in (1, 'long') else -1; ex = C[r[-1]] - s * c.SL[sym]
        out[d] = s * (ex - t['entry']) / t['entry'] - c.COST[sym] / t['entry']
    return out
picked = c.walkforward(raw['quantlab'], 1.0); capd = {}
for t in picked:
    if not (LO <= t['date'] <= HI): continue
    y = t['date'][:4]; q = capd.setdefault(y, dict(picked=0, kept=0, gross_all=0.0, net_all=0.0, gross_kept=0.0, net_kept=0.0, cost_all=0.0))
    q['picked'] += 1; q['gross_all'] += t['gross']; q['net_all'] += t['gross'] - t['cost']; q['cost_all'] += t['cost']
    if t['cost'] <= cap: q['kept'] += 1; q['gross_kept'] += t['gross']; q['net_kept'] += t['gross'] - t['cost']
out = dict(era=ERA, leg_NQ=leg('NQ', raw['quantlab']), leg_ES=leg('ES', c.quantlab('ES', **kw['quantlab'])), cap_diag={y: {k: round(v, 2) for k, v in q.items()} for y, q in sorted(capd.items())})
os.makedirs(os.path.join(ROOT, 'analysis', '_cache'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'analysis', '_cache', f'batch21_{ERA}.json'), 'w')); print('ok', len(out['leg_NQ']), len(out['leg_ES'])); print(json.dumps(out['cap_diag']))
