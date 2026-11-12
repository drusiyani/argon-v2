"""Analysis only (does not touch the race). Batch 6 (12 Nov 2026): Gemini's structural ideas (T7), run at Dru's request.
Trial count: about 155 ideas tested in total before this batch, so a lucky pass is likely; read results with that in mind.
Baseline = the FIXED package (batch 4). Pass mark fixed BEFORE the run, same as batch 5: ADOPT only if, in BOTH eras,
vs the fixed package: higher per-year return AND higher Sortino AND worst drop no more than 1 point deeper AND bootstrap
chance of a drop worse than -35% no more than 1 point higher. Each idea is tested alone.
  A1 Downside-volatility core (Wang & Yan 2021): core = min(1.5, median of the last 252 values / today's value) of the
     22-day downside realised volatility of the Nasdaq, all known a day early. Replaces the VXN core.
  A2 VXN core + recovery floor (Gemini's own rule, flagged): if the Nasdaq rose over the 21 days to two closes ago and
     VXN then was below its level 20 days before, core weight is at least 1.0.
  B1 QuantLab noise-band gate (Zarattini et al. 2024): a QuantLab trade is kept only if the price at entry is outside the
     14-day noise band in its direction (band = max/min of today's open and yesterday's close, times 1 +/- the average
     absolute move from the open to that minute over the previous 14 days).
  B2 Reweighting (Gemini's own weights from in-sample results, flagged): QuantLab x0.5, noise band x1, ATR band x1.5,
     expiry x1 on the package's half size.
  C  Pyramiding gate (Gemini's own +0.5R trigger, flagged): among QuantLab / noise band / ATR band, the first trade in a
     direction each day is taken; a later same-direction trade only if the first is still open and at least +0.5R in
     profit at that minute."""
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



trades = P.book(1.0); base = build('NQ', 'vxn.csv', 'vxn', trades)
D, dl0, _ = c.daily('NQ'); T, O, H, L, C, n, mins, days_, wd = c.prep('NQ')
MM = {}
def mm(d):
    if d not in MM:
        x = {}
        for i in D[d]['r']:
            if 570 <= mins[i] < 960: x[mins[i]] = (O[i], C[i])
        MM[d] = x
    return MM[d]
dl = base['dl']; ret = base['ret_fix']; k_of = {d: k for k, d in enumerate(dl)}
# A1 downside semivolatility core
sv = {}
for k in range(22, len(dl)):
    sv[dl[k]] = math.sqrt(252 / 22 * sum(min(0.0, ret.get(dl[j], 0.0)) ** 2 for j in range(k - 21, k + 1)))
wA1 = {}
for k in range(1, len(dl)):
    if k < 24 or dl[k - 2] not in sv: wA1[dl[k]] = 1.0; continue
    h = sorted(sv[dl[j]] for j in range(max(22, k - 254), k - 1) if dl[j] in sv); cur = sv[dl[k - 2]]
    wA1[dl[k]] = 1.5 if cur <= 0 else min(1.5, (h[len(h) // 2] if len(h) >= 60 else cur) / cur)
# A2 recovery floor
VX = csvmap('vxn.csv', 'vxn'); vk = sorted(VX); lvl = {}; x = 1.0
for d in dl[1:]: x *= 1 + ret[d]; lvl[d] = x
wA2 = {}
for k in range(1, len(dl)):
    w = base['w_fix'][dl[k]]
    if k >= 23:
        up = lvl[dl[k - 2]] / lvl[dl[k - 22]] - 1 > 0 if dl[k - 22] in lvl else False
        v2, _ = lastbefore(VX, vk, dl[k - 1]); v22, _ = lastbefore(VX, vk, dl[k - 21])
        if up and v2 and v22 and v2 < v22: w = max(1.0, w)
    wA2[dl[k]] = w
# B1 noise band gate for QuantLab
def nb_ok(t):
    d = t['date']; k = k_of.get(d); m = t['entry_min']
    if k is None or k < 15: return True
    today = mm(d); px = today.get(m - 1); op = today.get(570)
    if not px or not op: return True
    moves = []
    for j in range(k - 14, k):
        b = mm(dl[j]); a, z = b.get(570), b.get(m - 1)
        if a and z: moves.append(abs(z[1] / a[0] - 1))
    if len(moves) < 10: return True
    sg = sum(moves) / len(moves); pc = D[dl[k - 1]]['c']
    up, lo = max(op[0], pc) * (1 + sg), min(op[0], pc) * (1 - sg)
    return px[1] > up if t['side'] > 0 else px[1] < lo
# C pyramiding gate
BRK = ('quantlab', 'noiseband', 'atrband'); keepC = set()
byday = collections.defaultdict(list)
for i, t in enumerate(trades):
    if t['strat'] in BRK: byday[t['date']].append((t['entry_min'], i))
for d, lst in byday.items():
    first = {}
    for m, i in sorted(lst):
        t = trades[i]; s = 1 if t['side'] > 0 else -1
        if s not in first: first[s] = i; keepC.add(i); continue
        f = trades[first[s]]
        if 'entry' not in f or not (f['entry_min'] <= m < f['exit_min']): continue
        px = mm(d).get(m - 1)
        if px and (px[1] - f['entry']) * s / f['risk_pts'] >= 0.5: keepC.add(i)
WB2 = {'quantlab': 0.5, 'noiseband': 1.0, 'atrband': 1.5, 'expiry': 1.0}
def rules(fn):
    out = collections.defaultdict(float)
    for i, t in enumerate(trades): out[t['date']] += fn(i, t) * t.get('w', 1.0) * (t['gross'] - t['cost'])
    return out
R0 = rules(lambda i, t: 1.0)
RB1 = rules(lambda i, t: 0.0 if (t['strat'] == 'quantlab' and not nb_ok(t)) else 1.0)
RB2 = rules(lambda i, t: WB2.get(t['strat'], 1.0))
RC = rules(lambda i, t: 1.0 if (t['strat'] not in BRK or i in keepC) else 0.0)
first_day = min(t['date'] for t in trades); days = [d for d in dl[1:] if max(LO, first_day) <= d <= HI]
def pkg(R, W): return [W[d] * ret[d] + 0.5 * risk * R.get(d, 0.0) + base['f_fix'].get(d, 0.0) + base['tb'][d] for d in days]
SER = {'index alone': [ret[d] for d in days], 'package baseline': pkg(R0, base['w_fix']),
       'A1 downside-vol core': pkg(R0, wA1), 'A2 recovery floor': pkg(R0, wA2), 'B1 QuantLab noise gate': pkg(RB1, base['w_fix']),
       'B2 reweighting': pkg(RB2, base['w_fix']), 'C pyramiding gate': pkg(RC, base['w_fix'])}
hist = {k: metrics(v) for k, v in SER.items()}; bt = boot(SER); b0, bb = hist['package baseline'], bt['package baseline']
def ok(k):
    h, b = hist[k], bt[k]
    return h['cagr_pct'] > b0['cagr_pct'] and h['sortino'] > b0['sortino'] and h['worst_drop_pct'] >= b0['worst_drop_pct'] - 1 and b['chance_drop_worse_than_35_pct'] <= bb['chance_drop_worse_than_35_pct'] + 1
extra = dict(quantlab_trades=sum(1 for t in trades if t['strat'] == 'quantlab' and days[0] <= t['date'] <= days[-1]),
             quantlab_kept_by_B1=sum(1 for t in trades if t['strat'] == 'quantlab' and days[0] <= t['date'] <= days[-1] and nb_ok(t)),
             breakout_trades=sum(1 for t in trades if t['strat'] in BRK and days[0] <= t['date'] <= days[-1]),
             breakout_kept_by_C=sum(1 for i, t in enumerate(trades) if t['strat'] in BRK and days[0] <= t['date'] <= days[-1] and i in keepC))
out = dict(era=ERA, note=__doc__, range=[days[0], days[-1]], extra=extra, history=hist, bootstrap=bt,
           verdict_this_era={k: ('PASS' if ok(k) else 'FAIL') for k in SER if k not in ('index alone', 'package baseline')})
json.dump(out, open(os.path.join(ROOT, 'analysis', f'batch6_{ERA}.json'), 'w'), indent=1)
print(json.dumps(out['verdict_this_era']), json.dumps(extra))
