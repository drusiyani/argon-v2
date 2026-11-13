"""Batch 11 (13 Nov 2026). Rules and pass marks: analysis/BATCH11_PREREG.md (committed before this file ran)."""

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




trades = P.book(1.0); base = build('NQ', 'vxn.csv', 'vxn', trades); dl = base['dl']; pos = {d: k for k, d in enumerate(dl)}
first = min(t['date'] for t in trades); days = [d for d in dl[1:] if max(LO, first) <= d <= HI]
D, _, atr = c.daily('NQ')
core = {d: base['w_fix'][d] * base['ret_fix'][d] + base['f_fix'].get(d, 0.0) for d in dl[1:]}
def net(t): return t.get('w', 1.0) * (t['gross'] - t['cost'])
def agree(t):                        # +1 with the overnight gap, -1 against, 0 unknown / not a momentum rule
    if t['strat'] == 'expiry' or t['sym'] != 'NQ': return 0
    k = pos.get(t['date'], 0)
    if k == 0: return 0
    g = D[t['date']]['o'] - D[dl[k - 1]]['c']; s = 1 if t['side'] in (1, 'long') else -1
    return 0 if g == 0 else (1 if g * s > 0 else -1)
def series(wmap, k=1.0):
    R = collections.defaultdict(float)
    for t in trades: R[t['date']] += wmap[agree(t)] * net(t)
    return [k * (core[d] + 0.5 * risk * R.get(d, 0.0)) + base['tb'][d] for d in days]
SER = {'package baseline': series({1: 1, -1: 1, 0: 1}), 'K1 gap reallocation': series({1: 1.5, -1: 0.5, 0: 1}), 'K2 skip against-gap': series({1: 1, -1: 0, 0: 1})}
hist_ = {k: metrics(v) for k, v in SER.items()}; bt = boot(SER); b0, bb = hist_['package baseline'], bt['package baseline']
def verdict(nm):
    h, b = hist_[nm], bt[nm]
    return 'PASS' if (h['cagr_pct'] > b0['cagr_pct'] and h['sortino'] > b0['sortino'] and h['worst_drop_pct'] >= b0['worst_drop_pct'] - 1
                      and b['chance_drop_worse_than_35_pct'] <= bb['chance_drop_worse_than_35_pct'] + 1) else 'FAIL'
def boot21(SER, draws=1000, B=21, seed=20261111):
    rng = random.Random(seed); N = len(next(iter(SER.values()))); res = {k: [] for k in SER}
    for _ in range(draws):
        idx = []
        while len(idx) < N: st = rng.randrange(0, N - B); idx.extend(range(st, st + B))
        idx = idx[:N]
        for k, v in SER.items():
            eq, peak, dd = 1.0, 1.0, 0.0
            for i in idx: eq *= 1 + v[i]; peak = max(peak, eq); dd = min(dd, eq / peak - 1)
            res[k].append(dd)
    return {k: round(100 * sum(x < -.35 for x in v) / draws, 1) for k, v in res.items()}
LEV = {'1.25x baseline': series({1: 1, -1: 1, 0: 1}, 1.25), '1.25x K1': series({1: 1.5, -1: 0.5, 0: 1}, 1.25), '1.25x K2': series({1: 1, -1: 0, 0: 1}, 1.25)}
lb = boot21(LEV); lev = {k: dict(metrics(v), boot21_chance_drop_worse_than_35_pct=lb[k]) for k, v in LEV.items()}
ds = set(days); sub = {}
for nm, a, b in (('2010-17', '2010', '2018'), ('2018-20', '2018', '2021'), ('2021-26', '2021', '2027')):
    for g, lab in ((1, 'with'), (-1, 'against')):
        x = [net(t) for t in trades if t['date'] in ds and a <= t['date'] < b and agree(t) == g]
        if x: sub[f'{nm} {lab}'] = dict(trades=len(x), avg_R=round(sum(x) / len(x), 3), total_R=round(sum(x), 1))
out = dict(era=ERA, range=[days[0], days[-1]], verdict_this_era={k: verdict(k) for k in list(SER)[1:]}, history=hist_, bootstrap=bt, sub_periods=sub, leverage_1_25x=lev)
json.dump(out, open(os.path.join(ROOT, 'analysis', f'batch11_{ERA}.json'), 'w'), indent=1)
print(out['verdict_this_era']); [print(' ', k, v, bt[k]['chance_drop_worse_than_35_pct']) for k, v in hist_.items()]; [print(' ', k, v) for k, v in lev.items()]; print(sub)
