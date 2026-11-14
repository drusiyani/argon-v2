"""Batch 14 step 1 (run once per era): package pieces, every trade, the 28 new features per Nasdaq trade, and the S&P trades.
Saved to analysis/_cache/ for batch14.py. No test here. See BATCH14_PREREG.md."""

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




import pickle, gzip, glob, bisect, statistics, datetime as dt
from zoneinfo import ZoneInfo
NYZ = ZoneInfo('America/New_York'); clip = lambda v, a: max(-a, min(a, v))
trades = P.book(1.0); base = build('NQ', 'vxn.csv', 'vxn', trades); dl = base['dl']; pos = {d: k for k, d in enumerate(dl)}
first = min(t['date'] for t in trades); days = [d for d in dl[1:] if max(LO, first) <= d <= HI]
def overnight(S):
    T, O, H, L, C, n, mins, cdays, wd = c.prep(S); idx = collections.defaultdict(list); on = {}
    for i in range(n):
        if mins[i] < 570: idx[cdays[i]].append(i)
    for d, ix in idx.items(): on[d] = (max(H[i] for i in ix), min(L[i] for i in ix), O[ix[0]])
    return on
D, _, atr = c.daily('NQ'); DE, dlE, atrE = c.daily('ES'); on = overnight('NQ'); onE = overnight('ES')
NB, _ = c.nb_load('NQ'); ESB, _ = c.nb_load('ES'); nk = sorted(NB); nki = {d: i for i, d in enumerate(nk)}
cumv = {}
for d in nk:
    s = 0.0; a = []
    for b in NB[d]: s += b[5]; a.append(s)
    cumv[d] = a
# pre-market volume and the 08:30 reaction, from the raw minutes (as batch 10)
dirn = os.path.join(ROOT, 'data', 'databento' if ERA == 'databento' else ERA); c829, c834, pv = {}, {}, collections.defaultdict(float); off = {}
for f in sorted(glob.glob(os.path.join(dirn, 'NQ_*.csv.gz'))):
    with gzip.open(f, 'rt') as fh:
        for r in csv.DictReader(fh):
            ts = r['ts_event']; dk = ts[:13]
            if dk not in off:
                u = dt.datetime(int(ts[:4]), int(ts[5:7]), int(ts[8:10]), int(ts[11:13]), tzinfo=dt.timezone.utc).astimezone(NYZ); off[dk] = (u.date().isoformat(), u.hour)
            d, hr = off[dk]; m = hr * 60 + int(ts[14:16])
            if 240 <= m < 570: pv[d] += float(r['volume'] or 0)
            if m == 509: c829[d] = float(r['close'])
            elif m == 514: c834[d] = float(r['close'])
# outside data (FRED), read strictly before the previous trading day
def fred(name):
    out = {}
    for r in csv.DictReader(open(os.path.join(ROOT, 'analysis', 'ext_fred', name + '.csv'))):
        try: out[r['observation_date']] = float(r[name])
        except ValueError: pass
    return out, sorted(out)
F = {k: fred(k) for k in ('DGS10', 'DGS2', 'DTWEXBGS', 'USEPUINDXD', 'DCOILWTICO')}
VIX = csvmap('VIXCLS.csv', 'vixcls'); VXV = csvmap('VXVCLS.csv', 'vxvcls'); VXN = csvmap('vxn.csv', 'vxn'); F['VIX'] = (VIX, sorted(VIX)); F['VXV'] = (VXV, sorted(VXV)); F['VXN'] = (VXN, sorted(VXN))
def rd(k, p, back=0):
    src, keys = F[k]; i = bisect.bisect_left(keys, p) - 1 - back
    return src[keys[i]] if i >= 0 else None
def outside(p):
    y10, y10b, y2 = rd('DGS10', p), rd('DGS10', p, 5), rd('DGS2', p); us, usb = rd('DTWEXBGS', p), rd('DTWEXBGS', p, 5); oil, oilb = rd('DCOILWTICO', p), rd('DCOILWTICO', p, 5)
    src, keys = F['USEPUINDXD']; i = bisect.bisect_left(keys, p) - 1; ep = 1.0
    if i >= 370: ep = statistics.mean(src[k] for k in keys[i - 6:i + 1]) / statistics.median(src[k] for k in keys[i - 364:i + 1])
    vx, v3, vn, vnb = rd('VIX', p), rd('VXV', p), rd('VXN', p), rd('VXN', p, 5)
    return [(y10 - y10b) if (y10 is not None and y10b is not None) else 0.0, (y10 - y2) if (y10 is not None and y2 is not None) else 0.0,
            (us / usb - 1) if (us and usb) else 0.0, ep, clip(oil / oilb - 1, 0.5) if (oil and oilb and oil > 1 and oilb > 1) else 0.0,
            (vx / v3) if (vx and v3) else 1.0, (vn / vnb - 1) if (vn and vnb) else 0.0]
def third_friday(y, m):
    d0 = dt.date(y, m, 1); return d0 + dt.timedelta(days=(4 - d0.weekday()) % 7 + 14)
FOMC = set(c.FOMC)
def calendar(d):
    k = pos[d]; x = dt.date.fromisoformat(d); tf = third_friday(x.year, x.month); nx = dl[k + 1] if k + 1 < len(dl) else None; nx2 = dl[k + 2] if k + 2 < len(dl) else None
    return [1.0 if tf - dt.timedelta(days=4) <= x <= tf else 0.0, 1.0 if (nx in FOMC) else 0.0, 1.0 if (k > 0 and dl[k - 1] in FOMC) else 0.0,
            1.0 if (nx is None or nx[:7] != d[:7] or nx2 is None or nx2[:7] != d[:7]) else 0.0, 1.0 if (k < 2 or dl[k - 1][:7] != d[:7] or dl[k - 2][:7] != d[:7]) else 0.0] + [1.0 if x.weekday() == w_ else 0.0 for w_ in (1, 2, 3, 4)]
pvk = [d for d in dl if d in pv]; pvi = {d: i for i, d in enumerate(pvk)}
def premarket(d):
    a = atr[d]; i = pvi.get(d); r = 1.0
    if i is not None and i >= 10:
        med = statistics.median(pv[q] for q in pvk[max(0, i - 20):i]); r = clip(pv[d] / med, 5) if med > 0 else 1.0
    sh = abs(c834[d] / c829[d] - 1) * D[d]['o'] / a if (d in c829 and d in c834) else 0.0; onh, onl, ono = on.get(d, (D[d]['o'],) * 3)
    return r, sh, (onh - onl) / a, (D[d]['o'] - ono) / a
EXT = {}; dcache = {}
for ti, t in enumerate(trades):
    d = t['date']
    if t['strat'] == 'expiry' or t['sym'] != 'NQ' or d not in NB or d not in atr or pos.get(d, 0) < 1: continue
    B = NB[d]; ms = [b[0] for b in B]; j = bisect.bisect_left(ms, t['entry_min'])
    if j < 2: continue
    a = atr[d]; s = 1 if t['side'] in (1, 'long') else -1; px = B[j - 1][4]; op = B[0][1]; hi = max(b[2] for b in B[:j]); lo = min(b[3] for b in B[:j])
    sv = cumv[d][j - 1]; vw = sum((b[2] + b[3] + b[4]) / 3 * b[5] for b in B[:j]) / sv if sv > 0 else px
    orh = max(b[2] for b in B[:5]); orl = min(b[3] for b in B[:5]); rv = sum(abs(B[k][4] - B[k - 1][4]) for k in range(1, j)) / (j - 1) / a * 100
    i = nki[d]; cv = [cumv[q][min(j, len(cumv[q])) - 1] for q in nk[max(0, i - 20):i]]; med = statistics.median(cv) if len(cv) >= 10 else 0; vr = clip(sv / med, 5) if med > 0 else 1.0
    es = 0.0
    if d in ESB and d in atrE:
        EB = ESB[d]; je = bisect.bisect_left([b[0] for b in EB], t['entry_min'])
        if je >= 1: es = s * (EB[je - 1][4] - EB[0][1]) / atrE[d]
    x1 = s * (px - op) / a
    if d not in dcache: dcache[d] = (premarket(d), calendar(d), outside(dl[pos[d] - 1]))
    (pr, sh, onr, pdir), cal, out = dcache[d]
    EXT[ti] = [clip(x1, 5), s * (2 * (px - lo) / (hi - lo) - 1) if hi > lo else 0.0, clip(s * (px - vw) / a, 5), (orh - orl) / a, rv, vr, clip(es, 5), clip(x1 - es, 5),
               pr, sh, onr, clip(s * pdir, 5)] + cal + out
kw = P.CONFIG['strategies']
es_tr = c.walkforward(c.quantlab('ES', **kw['quantlab'])) + c.walkforward(c.noiseband('ES', **kw['noiseband'])) + c.atrband('ES', **kw['atrband'])
es_tr = [t for t in es_tr if t['cost'] <= cap and LO <= t['date'] <= HI]
os.makedirs(os.path.join(ROOT, 'analysis', '_cache'), exist_ok=True)
pickle.dump(dict(era=ERA, risk=risk, days=days, dl=dl, trades=trades, w=base['w_fix'], ret=base['ret_fix'], fomc=base['f_fix'], tb=base['tb'],
                 D={d: (D[d]['o'], D[d]['h'], D[d]['l'], D[d]['c']) for d in D}, atr=atr, on=on, ext=EXT,
                 es=dict(trades=es_tr, dl=dlE, D={d: (DE[d]['o'], DE[d]['h'], DE[d]['l'], DE[d]['c']) for d in DE}, atr=atrE, on=onE)),
            open(os.path.join(ROOT, 'analysis', '_cache', f'batch14_{ERA}.pkl'), 'wb'))
print('ok', len(trades), len(EXT), len(es_tr), len(next(iter(EXT.values()))))
