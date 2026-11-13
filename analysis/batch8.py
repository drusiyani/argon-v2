"""Batch 8 (13 Nov 2026). Rules and pass marks: analysis/BATCH8_PREREG.md (committed before this file ran)."""

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




import math as _m
FOMC = set(c.FOMC)
def cal_rows(S):
    T, O, H, L, C, n, mins, days, wd = c.prep(S); D, dl, atr = c.daily(S); return T, O, H, L, C, mins, D, dl, atr

def spread_rule():
    NQ = cal_rows('NQ'); ES = cal_rows('ES'); skN, skE = skipset('NQ'), skipset('ES')
    _, ON, HN, LN, CN, mN, DN, dlN, _ = NQ; _, OE, HE, LE, CE, mE, DE, dlE, _ = ES
    days = [d for d in dlN if d in DE]; hist_r, hist_x = [], []; out = []
    for d in days:
        if d in FOMC or d in skN['roll'] | skN['bad'] | skE['roll'] | skE['bad']: continue
        rn = {mN[i]: i for i in DN[d]['r']}; re_ = {mE[i]: i for i in DE[d]['r']}
        common = sorted(set(rn) & set(re_)); 
        if len(common) < 300: continue
        no, eo = ON[DN[d]['r'][0]], OE[DE[d]['r'][0]]
        beta = sig = None
        if len(hist_r) >= 40:
            h = hist_r[-60:]; mx = sum(b for _, b in h) / len(h); my = sum(a for a, _ in h) / len(h)
            vx = sum((b - mx) ** 2 for _, b in h); beta = sum((a - my) * (b - mx) for a, b in h) / vx if vx > 0 else None
        if len(hist_x) >= 20: sig = _m.sqrt(sum(v * v for v in hist_x[-20:]) / 20)
        xf = lambda m, b: _m.log(CN[rn[m]] / no) - b * _m.log(CE[re_[m]] / eo)
        if beta is not None and sig and sig > 0:
            trade_ = None
            for m in common:
                if not (614 <= m <= 899 and (m - 570) % 15 == 14): continue
                x = xf(m, beta)
                if abs(x) >= 1.0 * sig:
                    k = common.index(m)
                    if k + 1 >= len(common): break
                    m1 = common[k + 1]; s = 1 if x > 0 else -1
                    xe = _m.log(ON[rn[m1]] / no) - beta * _m.log(OE[re_[m1]] / eo)
                    npx, epx = ON[rn[m1]], OE[re_[m1]]
                    cost = 0.75 / npx + abs(beta) * 0.5 / epx; xx, why = None, 'close'
                    for mm in common[k + 1:]:
                        if mm > 954: break
                        xc = xf(mm, beta); xx = xc
                        if s * xc >= 2.0 * sig: why = 'stop'; cost += 0.25 / npx + abs(beta) * 0.25 / epx; break
                        if s * xc <= 0: why = 'target'; break
                    if xx is None: break
                    trade_ = dict(date=d, side=-s, beta=round(beta, 3), why=why, gross=s * (xe - xx) / sig, cost=cost / sig)
                    break
            if trade_ and trade_['cost'] <= cap: out.append(trade_)
        hist_r.append((_m.log(DN[d]['c'] / DN[d]['o']), _m.log(DE[d]['c'] / DE[d]['o'])))
        lastm = [m for m in common if m <= 959][-1]; hist_x.append(xf(lastm, beta if beta is not None else 1.0) if beta is not None else
                                                                   _m.log(CN[rn[lastm]] / no) - _m.log(CE[re_[lastm]] / eo))
    return out

def fade_rule(calm):
    _, O, H, L, C, mins, D, dl, atr = cal_rows('NQ'); sk = skipset('NQ'); tk = 0.25; out = []
    for d in dl:
        if d not in atr or not calm.get(d) or d in FOMC or d in sk['roll'] | sk['bad']: continue
        r = D[d]['r']; band = 0.35 * atr[d]; acc = 0.0
        for k, i in enumerate(r):
            acc += (H[i] + L[i] + C[i]) / 3; A = acc / (k + 1); m = mins[i]
            if not (614 <= m <= 899 and (m - 570) % 15 == 14): continue
            s = -1 if C[i] >= A + band else (1 if C[i] <= A - band else 0)
            if not s or k + 1 >= len(r): continue
            j = r[k + 1]; entry = O[j] + s * tk; stop = entry - s * band; tgt = A
            if (tgt - entry) * s <= 0: break
            ex = None
            for q in r[k + 1:]:
                if mins[q] > 954: break
                if (L[q] <= stop) if s == 1 else (H[q] >= stop): ex = stop - s * tk; break
                if (H[q] >= tgt + tk) if s == 1 else (L[q] <= tgt - tk): ex = tgt; break
                ex_close = C[q]
            if ex is None: ex = ex_close
            t = dict(date=d, side=s, gross=(ex - entry) * s / band, cost=0.75 / band)
            if t['cost'] <= cap: out.append(t)
            break
    return out

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

def corr(a, b):
    n = len(a); ma, mb = sum(a) / n, sum(b) / n
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / _m.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))

trades = P.book(1.0); base = build('NQ', 'vxn.csv', 'vxn', trades)
R0 = collections.defaultdict(float)
for t in trades: R0[t['date']] += t.get('w', 1.0) * (t['gross'] - t['cost'])
first = min(t['date'] for t in trades); days = [d for d in base['dl'][1:] if max(LO, first) <= d <= HI]
calm = {d: base['w_fix'][d] > 1.0 for d in base['w_fix']}
S1 = spread_rule(); S2 = fade_rule(calm)
def daily_R(tr):
    o = collections.defaultdict(float)
    for t in tr: o[t['date']] += t['gross'] - t['cost']
    return o
R1, R2 = daily_R(S1), daily_R(S2)
pk = lambda k=1.0, extra=(): [k * (base['w_fix'][d] * base['ret_fix'][d] + 0.5 * risk * R0.get(d, 0.0) + base['f_fix'].get(d, 0.0)
                              + sum(0.5 * risk * X.get(d, 0.0) for X in extra)) + base['tb'][d] for d in days]
SER = {'package baseline': pk(), 'package + S1 spread': pk(extra=(R1,)), 'package + S2 fade': pk(extra=(R2,)),
       'S1 alone (1% risk)': [risk * R1.get(d, 0.0) for d in days], 'S2 alone (1% risk)': [risk * R2.get(d, 0.0) for d in days]}
hist = {k: metrics(v) for k, v in SER.items()}; bt = boot({k: SER[k] for k in list(SER)[:3]})
b0, bb = hist['package baseline'], bt['package baseline']
def verdict(name):
    h, b = hist[name], bt[name]
    return 'PASS' if (h['cagr_pct'] > b0['cagr_pct'] and h['sortino'] > b0['sortino'] and h['worst_drop_pct'] >= b0['worst_drop_pct'] - 1
                      and b['chance_drop_worse_than_35_pct'] <= bb['chance_drop_worse_than_35_pct'] + 1) else 'FAIL'
def stats(tr):
    inr = [t for t in tr if max(LO, first) <= t['date'] <= HI]; g = [t['gross'] - t['cost'] for t in inr]
    return dict(trades=len(g), total_R=round(sum(g), 1), avg_R=round(sum(g) / len(g), 3) if g else None,
                win_pct=round(100 * sum(x > 0 for x in g) / len(g), 1) if g else None,
                exits=dict(collections.Counter(t.get('why', '') for t in inr)))
bad = [i for i, d in enumerate(days) if SER['package baseline'][i] < 0]
diag = {nm: dict(corr_with_package=round(corr(SER[nm], SER['package baseline']), 3),
                 R_on_package_down_days=round(sum(X.get(days[i], 0.0) for i in bad), 1), **stats(tr))
        for nm, X, tr in (('S1 alone (1% risk)', R1, S1), ('S2 alone (1% risk)', R2, S2))}
v = {'S1 spread': verdict('package + S1 spread'), 'S2 fade': verdict('package + S2 fade')}
out = dict(era=ERA, range=[days[0], days[-1]], verdict_this_era=v, history=hist, bootstrap=bt, diagnostics=diag)
# leverage re-test numbers are computed for every combo, but only COUNT for rules that pass in both eras (see prereg)
L = {}
for nm, extra in (('S1', (R1,)), ('S2', (R2,)), ('S1+S2', (R1, R2)), ('none', ())):
    s = pk(1.25, extra); L[f'1.25x package + {nm}'] = dict(worst_drop_pct=metrics(s)['worst_drop_pct'], cagr_pct=metrics(s)['cagr_pct'], sharpe=metrics(s)['sharpe'],
                                                         boot21_chance_drop_worse_than_35_pct=boot21({'x': s})['x'])
out['leverage_1_25x'] = L
json.dump(out, open(os.path.join(ROOT, 'analysis', f'batch8_{ERA}.json'), 'w'), indent=1)
print(json.dumps(dict(v=v, hist=hist, boot={k: x['chance_drop_worse_than_35_pct'] for k, x in bt.items()}, diag=diag, lev=L), indent=1))
