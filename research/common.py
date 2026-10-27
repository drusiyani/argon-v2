"""Argon v2 research: shared helpers and the 4 portfolio strategies, rebuilt with TRADE-LEVEL output.

Every strategy returns a list of trades (dicts): strat, sym, date, month, variant, side, entry_min, exit_min,
risk_pts, gross (R before costs), cost (R of one round-trip cost). R after costs = gross - cx*cost.
With default settings each one reproduces the original scripts (research/orig_qb.py, research/orig_deep.py and the
ATR band / expiry code from the handover). Optional keyword settings are the adjustments in ADJUSTMENTS.md.

LOCKBOX: by default nothing from 2025-01-01 onward is even simulated. Only ARGON_LOCKBOX=open (set ONCE, when the
survivors are opened) or ARGON_FULL=1 (only used to re-check the already-published base numbers) lifts it."""
import os, sys, gzip, csv, glob, collections, datetime as dt, statistics as stt, random
ROOT = os.environ.get('ARGON_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT + '/engine')
from calendar_us import FOMC, FOMC_EXIT_MIN
from zoneinfo import ZoneInfo
NY = ZoneInfo('America/New_York')
COST = {'NQ': 0.75, 'ES': 0.5}; SL = {'NQ': 0.25, 'ES': 0.25}
FIRST_MONTH = '2021-07'; TEST_END = '2024-12'; LOCK_START = '2025-01'; FULL_END = '2026-09'
OPEN = os.environ.get('ARGON_LOCKBOX') == 'open' or os.environ.get('ARGON_FULL') == '1'
LAST_DAY = '9999-12-31' if OPEN else '2024-12-31'
def allowed(d): return d <= LAST_DAY

# ---------------------------------------------------------------- data
_G = None
def m1():
    global _G
    if _G is None:
        src = open(ROOT + '/engine/backtest_core.py').read().split('# ---------------- swings & structure per tf')[0]
        g = {'__file__': ROOT + '/engine/x.py'}; exec(src, g); _G = g
    return _G['M1'], _G['ROLL_DAYS']
_P = {}
def prep(s):
    """T,O,H,L,C,n,mins,days,wd with New York minutes-of-day, exactly as in orig_qb.py."""
    if s in _P: return _P[s]
    M1, _ = m1(); T, O, H, L, C = M1[s]; n = len(T); off = {}; mins = [0] * n; days = [''] * n; wd = [0] * n; iso = {}
    base = dt.date(1970, 1, 1).toordinal()
    for i in range(n):
        t = int(T[i]); dk = t // 86400
        if dk not in off: off[dk] = dt.datetime.fromtimestamp(t, NY).utcoffset().total_seconds()
        loc = t + int(off[dk]); mins[i] = (loc % 86400) // 60; od = base + loc // 86400
        if od not in iso: x = dt.date.fromordinal(od); iso[od] = (x.isoformat(), x.weekday())
        days[i], wd[i] = iso[od]
    _P[s] = (T, O, H, L, C, n, mins, days, wd); return _P[s]
def roll(s): return m1()[1].get(s, ())
_D = {}
def daily(s):
    """Regular-session daily bars + ATR(14) (true range) from the 14 PREVIOUS days (no lookahead)."""
    if s in _D: return _D[s]
    P = prep(s); T, O, H, L, C, n, mins, days, wd = P; idx = collections.defaultdict(list)
    for i in range(n): idx[days[i]].append(i)
    D = {}
    for d in sorted(idx):
        r = [i for i in idx[d] if 570 <= mins[i] < 960]
        if len(r) > 300: D[d] = dict(r=r, o=O[r[0]], h=max(H[i] for i in r), l=min(L[i] for i in r), c=C[r[-1]])
    dl = sorted(D); atr = {}
    for k in range(15, len(dl)):
        atr[dl[k]] = sum(max(D[dl[j]]['h'] - D[dl[j]]['l'], abs(D[dl[j]]['h'] - D[dl[j - 1]]['c']), abs(D[dl[j]]['l'] - D[dl[j - 1]]['c'])) for j in range(k - 14, k)) / 14
    _D[s] = (D, dl, atr); return _D[s]

def trade(strat, s, d, variant, side, emin, xmin, risk_pts, pnl_pts):
    return dict(strat=strat, sym=s, date=d, month=d[:7], variant=variant, side=side, entry_min=emin, exit_min=xmin,
                risk_pts=risk_pts, gross=pnl_pts / risk_pts, cost=COST[s] / risk_pts)

def walkx(P, s, sess, side, entry, stop, risk, trail=None, atrd=None, be=None, partial=None):
    """1-minute walk used by ATR band and expiry. Stop slippage 1 tick. With no extras it is the original walk()."""
    T, O, H, L, C, n, mins, days, wd = P; stp = stop; best = entry; got = None
    for x in sess:
        if (L[x] <= stp) if side == 1 else (H[x] >= stp):
            rest = (stp - side * SL[s] - entry) * side
            return (rest if got is None else 0.5 * got + 0.5 * rest), x
        if partial and got is None:
            tgt = entry + side * partial * risk
            if (H[x] >= tgt + SL[s]) if side == 1 else (L[x] <= tgt - SL[s]): got = partial * risk
        if x == sess[-1]:
            rest = (C[x] - entry) * side
            return (rest if got is None else 0.5 * got + 0.5 * rest), x
        best = max(best, H[x]) if side == 1 else min(best, L[x])
        if be and (best - entry) * side >= be * risk: stp = max(stp, entry) if side == 1 else min(stp, entry)
        if trail: ts = best - side * trail * atrd; stp = max(stp, ts) if side == 1 else min(stp, ts)
    return (C[sess[-1]] - entry) * side, sess[-1]

# ---------------------------------------------------------------- 1. QuantLab (first 5-min candle vs 12 EMA)
_B5 = {}
def bars5(s, ema_n):
    key = (s, ema_n)
    if key in _B5: return _B5[key]
    P = prep(s); T, O, H, L, C, n, mins, days, wd = P
    b5 = []; cur = None
    for i in range(n):
        k = int(T[i]) // 300
        if cur is None or k != cur[0]: cur = [k, i, i, O[i], H[i], L[i], C[i]]; b5.append(cur)
        else: cur[2] = i; cur[4] = max(cur[4], H[i]); cur[5] = min(cur[5], L[i]); cur[6] = C[i]
    ema = []; e = None; a = 2 / (ema_n + 1)
    for b in b5: e = b[6] if e is None else e + a * (b[6] - e); ema.append(e)
    atr5 = []; q = collections.deque(maxlen=14)
    for b in b5: q.append(b[4] - b[5]); atr5.append(sum(q) / len(q))
    rng = {}
    for b in b5:
        i = b[1]
        if 570 <= mins[i] < 960: d = days[i]; lo, hi = rng.get(d, (1e18, -1e18)); rng[d] = (min(lo, b[5]), max(hi, b[4]))
    dlist = sorted(rng); datr = {d: (sum(rng[x][1] - rng[x][0] for x in dlist[max(0, j - 14):j]) / min(14, j) if j else None) for j, d in enumerate(dlist)}
    _B5[key] = (b5, ema, atr5, datr); return _B5[key]

def ql_variants(chands=(2, 3), stops=('candle', 'atr')):
    return [(st, tr) for st in stops for tr in ('ema',) + tuple(f'ch{k}' for k in chands)]

def quantlab(s='NQ', ema=12, chands=(2, 3), stops=('candle', 'atr'), stop_atr=0.10, delay=0, pullback=None, concretum=False,
             te=None, partial=None, be=None, confirm=1, first=5, skip_fomc=False, flat=955):
    P = prep(s); T, O, H, L, C, n, mins, days, wd = P; b5, EMA, atr5, datr = bars5(s, ema); TK = SL[s]
    V = ql_variants(chands, stops); out = []; R = roll(s)
    first_bars = [j for j, b in enumerate(b5) if mins[b[1]] == 570]
    for j in first_bars:
        b = b5[j]; d = days[b[1]]
        if not allowed(d): break
        if d in R or not datr.get(d) or j + 1 >= len(b5) or mins[b5[j + 1][1]] != 575: continue
        if skip_fomc and d in FOMC: continue
        exit_m = FOMC_EXIT_MIN if d in FOMC else flat
        if te: exit_m = min(exit_m, te)
        sig_j = j; hi, lo = b[4], b[5]
        if first == 10:     # 9:30-9:40 candle instead
            if j + 2 >= len(b5) or mins[b5[j + 2][1]] != 580: continue
            sig_j = j + 1; hi = max(hi, b5[j + 1][4]); lo = min(lo, b5[j + 1][5])
        side = 1 if b5[sig_j][6] > EMA[sig_j] else -1
        ej = sig_j + 1 + delay                  # 5-min bar whose open we buy
        if ej >= len(b5) or days[b5[ej][1]] != d: continue
        entry_i = b5[ej][1]; entry = O[entry_i] + side * 2 * TK; start_j = ej; start_i = entry_i
        if pullback is not None:                # limit order back towards the first candle, must trade 1 tick through, by 10:00
            lim = O[entry_i] - side * pullback * (hi - lo); f = None
            for i in range(entry_i, n):
                if days[i] != d or mins[i] >= 600: break
                if (L[i] <= lim - TK) if side == 1 else (H[i] >= lim + TK): f = i; break
            if f is None: continue
            entry = lim; start_i = f; start_j = next(k for k in range(ej, len(b5)) if b5[k][1] <= f <= b5[k][2])
        if concretum:                           # wait for the first 5-min bar that closes against us, enter next bar open (by 10:30)
            f = None
            for k in range(ej, len(b5)):
                bb = b5[k]
                if days[bb[1]] != d or mins[bb[1]] >= 630: break
                if (bb[6] < bb[3]) if side == 1 else (bb[6] > bb[3]): f = k + 1; break
            if f is None or f >= len(b5) or days[b5[f][1]] != d: continue
            start_j = f; start_i = b5[f][1]; entry = O[start_i] + side * TK
        emin = mins[start_i]
        for vi, (stk, trk) in enumerate(V):
            stop = (lo if side == 1 else hi) if stk == 'candle' else entry - side * stop_atr * datr[d]
            risk = (entry - stop) * side
            if risk <= 0: continue
            stp = stop; best = entry; res = None; xm = None; got = None; across = 0
            for jj in range(start_j, len(b5)):
                bb = b5[jj]
                if days[bb[1]] != d: break
                for i in range(max(bb[1], start_i), bb[2] + 1):
                    m = mins[i]
                    if m >= exit_m: res = (C[i] - entry) * side; xm = m; break
                    if (L[i] <= stp) if side == 1 else (H[i] >= stp): res = (stp - side * (3 if m < 585 else 1) * TK - entry) * side; xm = m; break
                    if partial and got is None:
                        tgt = entry + side * partial * risk
                        if (H[i] >= tgt + TK) if side == 1 else (L[i] <= tgt - TK): got = partial * risk
                if res is not None: break
                best = max(best, bb[4]) if side == 1 else min(best, bb[5])
                if be and (best - entry) * side >= be * risk: stp = max(stp, entry) if side == 1 else min(stp, entry)
                if trk == 'ema':
                    if (bb[6] < EMA[jj]) if side == 1 else (bb[6] > EMA[jj]):
                        across += 1
                        if across >= confirm:
                            nxt = bb[2] + 1; res = ((O[nxt] if nxt < n else bb[6]) - side * TK - entry) * side; xm = mins[min(nxt, n - 1)]; break
                    else: across = 0
                else:
                    k = float(trk[2:]); ts = best - side * k * atr5[jj]
                    stp = max(stp, ts) if side == 1 else min(stp, ts)
            if res is None: continue
            if got is not None: res = 0.5 * got + 0.5 * res
            out.append(trade('quantlab', s, d, vi, side, emin, xm, risk, res))
    return out

# ---------------------------------------------------------------- 2. Noise band (Zarattini/Aziz/Barbon), from orig_deep.py part B
_NB = {}
def nb_load(s):
    if s in _NB: return _NB[s]
    days = collections.defaultdict(dict); off = {}; iid = {}
    for f in sorted(glob.glob(f'{ROOT}/data/databento/{s}_*.csv.gz')):
        with gzip.open(f, 'rt') as fh:
            r = csv.reader(fh); h = next(r); iv = h.index('volume'); ii = h.index('instrument_id')
            for row in r:
                ts = row[0]; d0 = ts[:10]
                if d0 not in off: off[d0] = dt.datetime(int(d0[:4]), int(d0[5:7]), int(d0[8:10]), 12, tzinfo=dt.timezone.utc).astimezone(NY).utcoffset().total_seconds() / 60
                m = int(ts[11:13]) * 60 + int(ts[14:16]) + int(off[d0]); day = d0
                if m < 0: m += 1440; day = (dt.date.fromisoformat(d0) - dt.timedelta(days=1)).isoformat()
                if 570 <= m < 960:
                    days[day][m] = (m, float(row[4]), float(row[5]), float(row[6]), float(row[7]), float(row[iv])); iid.setdefault(day, row[ii])
    out = {d: sorted(v.values()) for d, v in days.items() if len(v) >= 300 and min(v) == 570}   # one bar per minute (2026-09 file overlaps 2026-partial)
    keys = sorted(out); rl = {b for a, b in zip(keys, keys[1:]) if iid[a] != iid[b]}
    _NB[s] = (out, rl); return _NB[s]

def noiseband(s='NQ', look=14, freqs=(30, 60), mults=(1.0, 1.5), stops=('band', 'vwap'), start=600, cutoff=930, flat=955,
              confirm=False, trail=None, te=None, skip_fomc=False, fomc_flat=False):
    D, RL = nb_load(s); K = sorted(D); out = []; TK = SL[s]
    V = [(f, m, st) for f in freqs for m in mults for st in stops]
    for i, d in enumerate(K):
        if not allowed(d): break
        if i < 21 or d in RL: continue
        if skip_fomc and d in FOMC: continue
        rows = D[d]; pc = D[K[i - 1]][-1][4]; op = rows[0][1]
        fl = flat
        if te: fl = min(fl, te)
        if fomc_flat and d in FOMC: fl = min(fl, FOMC_EXIT_MIN)
        sig_by_m = collections.defaultdict(list)
        for k in K[i - look:i]:
            r = D[k]; o = r[0][1]
            for x in r: sig_by_m[x[0]].append(abs(x[4] / o - 1))
        hi_ref = max(op, pc); lo_ref = min(op, pc)
        for vi, (freq, mult, stopk) in enumerate(V):
            pos = 0; ent = 0; unit = 0; pv = 0; vv = 0; em = 0; best = 0; pend = 0
            for x in rows:
                m, o, h, l, c, v = x; tp = (h + l + c) / 3; pv += tp * v; vv += v; vwap = pv / vv if vv else c
                if m >= fl:
                    if pos: out.append(trade('noiseband', s, d, vi, pos, em, m, unit, (c - ent) * pos))
                    pos = 0; break
                if pos and trail:       # optional trailing stop, checked every minute, in band units
                    best = max(best, h) if pos == 1 else min(best, l); ts = best - pos * trail * unit
                    if (l <= ts) if pos == 1 else (h >= ts):
                        out.append(trade('noiseband', s, d, vi, pos, em, m, unit, (ts - pos * TK - ent) * pos)); pos = 0; continue
                if m < start or (m - 570) % freq != freq - 1: continue
                sg = stt.mean(sig_by_m[m]) if sig_by_m[m] else None
                if not sg: continue
                up = hi_ref * (1 + mult * sg); dn = lo_ref * (1 - mult * sg)
                if pos == 1 and (c < up if stopk == 'band' else c < max(up, vwap)) or pos == -1 and (c > dn if stopk == 'band' else c > min(dn, vwap)):
                    out.append(trade('noiseband', s, d, vi, pos, em, m, unit, (c - pos * TK - ent) * pos)); pos = 0
                if pos == 0 and m <= cutoff and (c > up or c < dn):
                    sd = 1 if c > up else -1
                    if confirm and pend != sd: pend = sd; continue      # need two decisions in a row outside the band
                    pos = sd; ent = c + pos * TK; unit = max(1e-6, mult * sg * op); em = m + 1; best = ent
                elif pos == 0: pend = 0
            if pos and rows: out.append(trade('noiseband', s, d, vi, pos, em, rows[-1][0], unit, (rows[-1][4] - ent) * pos))
    return out

# ---------------------------------------------------------------- 3. ATR band
def atrband(s='NQ', mult=0.5, step=15, trail=None, be=None, partial=None, maxent=None, cutoff=None, te=None,
            stopmode='open', concretum=False, skip_fomc=False, flat=955):
    P = prep(s); T, O, H, L, C, n, mins, days, wd = P; D, dl, atr = daily(s); out = []; R = roll(s)
    for d in dl:
        if not allowed(d): break
        if d not in atr or d in R: continue
        if skip_fomc and d in FOMC: continue
        r = D[d]['r']; op = D[d]['o']; up = op + mult * atr[d]; dn = op - mult * atr[d]
        ex = FOMC_EXIT_MIN if d in FOMC else flat
        if te: ex = min(ex, te)
        k = 0; cnt = 0
        while k < len(r):
            i = r[k]
            if mins[i] >= ex: break
            if mins[i] % step == step - 1 and mins[i] >= 569 + step and k + 1 < len(r) and (cutoff is None or mins[i] < cutoff) and (maxent is None or cnt < maxent):
                side = 1 if C[i] > up else (-1 if C[i] < dn else 0)
                if side:
                    ek = k + 1
                    if concretum:      # wait (up to 15 min) for one 1-min candle closing against us, enter the next open
                        ek = next((q + 1 for q in range(k + 1, min(k + 16, len(r) - 1)) if ((C[r[q]] < O[r[q]]) if side == 1 else (C[r[q]] > O[r[q]]))), None)
                        if ek is None or mins[r[ek]] >= ex: k += 1; continue
                    e = r[ek]; entry = O[e] + side * SL[s]
                    stop = op if stopmode == 'open' else ((op + (up if side == 1 else dn)) / 2 if stopmode == 'mid' else entry - side * 0.25 * atr[d])
                    risk = (entry - stop) * side
                    if risk > 2 * SL[s]:
                        sess = [x for x in r[ek:] if mins[x] < ex + 1]
                        pnl, x = walkx(P, s, sess, side, entry, stop, risk, trail=trail, atrd=atr[d], be=be, partial=partial)
                        out.append(trade('atrband', s, d, 0, side, mins[e], mins[x], risk, pnl)); cnt += 1
                        k = r.index(x) + 1; continue
            k += 1
    return out

# ---------------------------------------------------------------- 4. Options-expiry reversal (third Friday, short 9:31 -> 12:00)
def opex(s='NQ', em=571, xm=720, stopk=0.25, nostop=False, cond=False, placebo=False, quarterly=False, skip_fomc_week=False):
    P = prep(s); T, O, H, L, C, n, mins, days, wd = P; D, dl, atr = daily(s); out = []
    for k, d in enumerate(dl):
        if not allowed(d): break
        dd = dt.date.fromisoformat(d)
        if not (dd.weekday() == 4 and ((15 <= dd.day <= 21) != placebo)) or d not in atr: continue
        if quarterly and dd.month not in (3, 6, 9, 12): continue
        if skip_fomc_week and any((dd - dt.timedelta(days=j)).isoformat() in FOMC for j in range(1, 5)): continue
        r = D[d]['r']; i0 = [i for i in r if mins[i] >= em]
        if cond and not D[d]['o'] > D[dl[k - 1]]['c']: continue
        sess = [i for i in i0 if mins[i] <= xm]
        if len(sess) < (100 if xm - em >= 100 else 30): continue
        entry = O[sess[0]] - SL[s]; risk = (H[r[0]] - L[r[0]]) + stopk * atr[d]; stop = entry + (1e9 if nostop else risk)
        pnl, x = walkx(P, s, sess, -1, entry, stop, risk)
        out.append(trade('expiry', s, d, 0, -1, mins[sess[0]], mins[x], risk, pnl))
    return out

# ---------------------------------------------------------------- walk-forward re-pick + scoring
def months_between(a, b):
    y, m = int(a[:4]), int(a[5:]); out = []
    while f'{y:04d}-{m:02d}' <= b: out.append(f'{y:04d}-{m:02d}'); m += 1; y += m > 12; m = (m - 1) % 12 + 1
    return out

def walkforward(trades, cx=1.0, look=6, pick='sum'):
    """Monthly re-pick: for each month use the variant with the best result over the previous `look` months
    (months = every month that has any trade, as in the originals). Returns only the chosen variant's trades."""
    if not trades: return []
    mon = collections.defaultdict(lambda: collections.defaultdict(float)); mlist = collections.defaultdict(lambda: collections.defaultdict(list))
    for t in trades: r = t['gross'] - cx * t['cost']; mon[t['variant']][t['month']] += r; mlist[t['variant']][t['month']].append(t)
    vs = sorted(mon); months = sorted({t['month'] for t in trades}); out = []
    def score(v, prev):
        xs = [mon[v][p] for p in prev]
        if pick == 'sum': return sum(xs)
        sd = stt.pstdev(xs); return stt.mean(xs) / sd if sd > 0 else 0
    for i, m in enumerate(months[look:], look):
        prev = months[i - look:i]; b = max(vs, key=lambda v: score(v, prev)); out += mlist[b][m]
    return out

def sharpe(x):
    if len(x) < 2: return 0.0
    sd = stt.stdev(x); return stt.mean(x) / sd * 12 ** .5 if sd > 0 else 0.0

def monthly(trades, months, cx=1.0):
    mm = collections.defaultdict(float)
    for t in trades: mm[t['month']] += t.get('w', 1.0) * (t['gross'] - cx * t['cost'])
    return [mm.get(m, 0.0) for m in months]

def write_csv(trades, path, cx=1.0):
    with open(path, 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['date', 'strategy', 'symbol', 'entry_time', 'exit_time', 'side', 'R', 'risk_pts', 'variant'])
        for t in sorted(trades, key=lambda t: (t['date'], t['entry_min'])):
            hm = lambda m: f'{m // 60:02d}:{m % 60:02d}'
            w.writerow([t['date'], t['strat'], t['sym'], hm(t['entry_min']), hm(t['exit_min']), 'long' if t['side'] == 1 else 'short',
                        round(t['gross'] - cx * t['cost'], 4), round(t['risk_pts'], 2), t['variant']])
