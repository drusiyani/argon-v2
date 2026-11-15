"""Batch 25 step 1 (run once per era): per-trade inputs for T1, T2, T3, T5, keyed by (date, rule, variant, entry minute).
Saved to analysis/_cache/ for batch25.py. See BATCH25_PREREG.md."""

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




import math, statistics, pickle
RULES = ('quantlab', 'noiseband', 'atrband'); trades = P.book(1.0); key = lambda t: (t['date'], t['strat'], t['variant'], t['entry_min'])
NB0, _ = c.nb_load('NQ'); NB = {d: {b[0]: b for b in v} for d, v in NB0.items()}; nk = sorted(NB); nki = {d: i for i, d in enumerate(nk)}
D, dl, atr = c.daily('NQ'); pos = {d: k for k, d in enumerate(dl)}; V = csvmap('vxn.csv', 'vxn'); vk = sorted(V)
def bar(d, s, n=5):
    B = NB[d]; bb = [B[m] for m in range(s, s + n) if m in B]
    if not bb: return None
    return (bb[0][1], max(b[2] for b in bb), min(b[3] for b in bb), bb[-1][4], sum(b[5] for b in bb))
SLOT = {}
def slot_hist(d, s):                    # previous 20 days' bars at the same slot
    i = nki[d]; out = []
    for q in reversed(nk[max(0, i - 40):i]):
        b = bar(q, s)
        if b: out.append(b)
        if len(out) == 20: break
    return out if len(out) == 20 else None
DAYR = {d: (max(b[2] for b in NB0[d]), min(b[3] for b in NB0[d])) for d in nk}
OUT = {}
for t in trades:
    if t['strat'] not in RULES or t['sym'] != 'NQ' or t['date'] not in NB: continue
    d = t['date']; s = t['entry_min'] - 5; tb = bar(d, s); h = slot_hist(d, s); i = nki[d]; stop = t['risk_pts']; r = {}
    # T1
    r['noise'] = statistics.mean(b[1] - b[2] for b in h) if h else None
    # T2
    pd20 = nk[max(0, i - 20):i]; adr = statistics.mean(DAYR[q][0] - DAYR[q][1] for q in pd20) if len(pd20) == 20 else None
    v, _ = lastbefore(V, vk, d); o = NB[d][570][1] if 570 in NB[d] else None
    idr = o * (v / 100) / math.sqrt(252) * 1.5958 if (v and o) else None
    used_b = [NB[d][m] for m in range(570, t['entry_min']) if m in NB[d]]
    used = max(b[2] for b in used_b) - min(b[3] for b in used_b) if used_b else None
    r['T2_skip'] = bool(adr is not None and idr is not None and used is not None and max(0.0, max(adr, idr) - used) < stop + 1.25)
    # T3
    if t['strat'] == 'quantlab':
        p_, q_ = NB[d].get(573), NB[d].get(574); prev = (p_[1], p_[2], p_[3], p_[4]) if p_ else None; cur = (q_[1], q_[2], q_[3], q_[4]) if q_ else None
    else:
        pb = bar(d, s - 5); prev = pb[:4] if pb else None; cur = tb[:4] if tb else None
    sp = None
    if prev and cur:
        e1 = 0.5 * (math.log(prev[1]) + math.log(prev[2])); e0 = 0.5 * (math.log(cur[1]) + math.log(cur[2])); c1 = math.log(prev[3])
        sp = min(1.5, math.sqrt(max(0.0, 4 * (c1 - e1) * (c1 - e0))) * cur[3])
    rv = tb[4] / statistics.mean(b[4] for b in h) if (tb and h and statistics.mean(b[4] for b in h) > 0) else None
    mult = max(1.0, 1.0 / math.sqrt(max(0.1, rv))) if rv is not None else 1.0
    r['fric3'] = (0.75 + max(0.50, sp if sp is not None else 0.0) * mult) / stop
    # T5
    if t['strat'] == 'quantlab': mm = [m for m in range(570, 575) if m in NB[d]]
    else: mm = [m for m in range(t['entry_min'] - 15, t['entry_min']) if m in NB[d]]
    er = None
    if len(mm) >= 3:
        B = [NB[d][m] for m in mm]; den = abs(B[0][4] - B[0][1]) + sum(abs(B[k][4] - B[k - 1][4]) for k in range(1, len(B)))
        er = abs(B[-1][4] - B[0][1]) / den if den > 0 else 1.0
    r['er'] = er; r['stop'] = stop; OUT[key(t)] = r
os.makedirs(os.path.join(ROOT, 'analysis', '_cache'), exist_ok=True)
pickle.dump(dict(era=ERA, x=OUT), open(os.path.join(ROOT, 'analysis', '_cache', f'batch25_{ERA}.pkl'), 'wb'))
print('ok', len(OUT), 'T1', sum(1 for v in OUT.values() if v['noise'] and v['stop'] < v['noise']), 'T2', sum(v['T2_skip'] for v in OUT.values()),
      'T5', sum(1 for v in OUT.values() if v['er'] is not None and v['er'] < 0.2), 'fric3 median', round(statistics.median(v['fric3'] for v in OUT.values()), 4))
