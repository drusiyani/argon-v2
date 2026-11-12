"""Analysis only (does not touch the race). Batch 4 (11 Nov 2026), from Gemini's red-team (T5) as reviewed by Claude.
Pass marks fixed BEFORE the run:
  F  Bug fixes, applied to everything: pre-FOMC exits 12:14 ET on the 2011-12 press-conference days (statement at 12:30);
     roll days use the day's own open-to-close move instead of 0; the vol index is read one day earlier (no 16:15 print
     used for a 16:00 trade); bootstrap blocks 63 days. The FIXED package "survives" if, in BOTH eras, it beats the
     Nasdaq alone on Sharpe, Sortino and worst drop.
  L  Long-only breakout rules (QuantLab, noise band, ATR band keep only long trades; expiry unchanged), from EdgeLab 2026.
     L1 standalone PASS: Sharpe >= today's rules + 0.15 and worst drop no deeper, both eras.
     L2 ADOPT in the package: package-with-long-only beats the fixed package on Sortino AND its bootstrap chance of a
     drop worse than -35% is no higher, both eras.
  V  Untouched check: the frozen fixed package rebuilt on the S&P (ES rules, VIX-managed ES core, pre-FOMC on ES,
     interest). PASS if it beats the S&P alone on Sharpe with a worst drop no deeper, both eras. Nothing is tuned for ES."""
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

def es_book():
    kw = P.CONFIG['strategies']
    tr = [dict(t, w=1.0) for t in c.walkforward(c.quantlab('ES', **kw['quantlab']))] + [dict(t, w=1.0) for t in c.walkforward(c.noiseband('ES', **kw['noiseband']))] + \
         [dict(t, w=1.0) for t in c.atrband('ES', **kw['atrband'])] + [dict(t, w=1.0) for t in c.opex('ES', **kw['expiry'])]
    return [t for t in tr if t['cost'] <= cap]

def series(B):
    first = min(B['bk']) if B['bk'] else LO
    days = [d for d in B['dl'][1:] if max(LO, first) <= d <= HI]
    R = lambda d: risk * B['bk'].get(d, 0.0); RL = lambda d: risk * B['bl'].get(d, 0.0)
    return days, {
        'index alone': [B['ret_fix'][d] for d in days],
        'rules (today)': [R(d) for d in days],
        'rules long-only (breakouts)': [RL(d) for d in days],
        'package BEFORE fixes': [B['w_old'][d] * B['ret_old'][d] + 0.5 * R(d) + B['f_old'].get(d, 0.0) + B['tb'][d] for d in days],
        'package FIXED': [B['w_fix'][d] * B['ret_fix'][d] + 0.5 * R(d) + B['f_fix'].get(d, 0.0) + B['tb'][d] for d in days],
        'package FIXED, long-only rules': [B['w_fix'][d] * B['ret_fix'][d] + 0.5 * RL(d) + B['f_fix'].get(d, 0.0) + B['tb'][d] for d in days]}

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

out = dict(era=ERA, note=__doc__)
nq = build('NQ', 'vxn.csv', 'vxn', P.book(1.0)); days, S = series(nq)
out['nasdaq'] = dict(range=[days[0], days[-1]], history={k: metrics(v) for k, v in S.items()}, bootstrap=boot(S))
try:
    es = build('ES', 'vix.csv', 'vix', es_book()); edays, ES = series(es)
    ES = {('S&P ' + k): v for k, v in ES.items() if k in ('index alone', 'rules (today)', 'package FIXED')}
    out['sp500_check'] = dict(range=[edays[0], edays[-1]], history={k: metrics(v) for k, v in ES.items()}, bootstrap=boot(ES))
except Exception as ex:
    out['sp500_check'] = dict(error=str(ex))
h = out['nasdaq']['history']; b = out['nasdaq']['bootstrap']
v = dict(F_package_survives_fixes=all(h['package FIXED'][m] > h['index alone'][m] for m in ('sharpe', 'sortino', 'worst_drop_pct')),
         L1_long_only_standalone=h['rules long-only (breakouts)']['sharpe'] >= h['rules (today)']['sharpe'] + 0.15 and h['rules long-only (breakouts)']['worst_drop_pct'] >= h['rules (today)']['worst_drop_pct'],
         L2_long_only_in_package=h['package FIXED, long-only rules']['sortino'] > h['package FIXED']['sortino'] and b['package FIXED, long-only rules']['chance_drop_worse_than_35_pct'] <= b['package FIXED']['chance_drop_worse_than_35_pct'])
if 'history' in out['sp500_check']:
    e = out['sp500_check']['history']; v['V_sp500_check'] = e['S&P package FIXED']['sharpe'] > e['S&P index alone']['sharpe'] and e['S&P package FIXED']['worst_drop_pct'] >= e['S&P index alone']['worst_drop_pct']
out['verdict_this_era'] = {k: ('PASS' if x else 'FAIL') for k, x in v.items()}
json.dump(out, open(os.path.join(ROOT, 'analysis', f'batch4_{ERA}.json'), 'w'), indent=1)
print(json.dumps(out['verdict_this_era'], indent=1))
