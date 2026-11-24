"""Batch 40: TikTok strategy sweep (rules: analysis/BATCH40_PREREG.md). Output: summary numbers only."""
import os, sys, json, math, datetime as dt, collections
import numpy as np
A = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(A)
sys.path.insert(0, A); sys.path.insert(0, os.path.join(ROOT, 'research')); sys.path.insert(0, os.path.join(ROOT, 'engine'))
SIMS = int(os.environ.get("B40_SIMS", 1000)); CHUNK = 10

class W: pass

def make_world(T, O, H, L, C, mins, days, rolls, atr_by_day, last_day):
    w = W(); w.T = np.asarray(T, dtype=np.int64)
    w.O, w.H, w.L, w.C = (np.asarray(x, dtype=float) for x in (O, H, L, C)); w.mins = np.asarray(mins, dtype=np.int64)
    uniq, inv = np.unique(np.asarray(days), return_inverse=True)
    o = np.array([dt.date.fromisoformat(u).toordinal() for u in uniq]); w.ords = o[inv]
    w.rollords = np.array(sorted(dt.date.fromisoformat(r).toordinal() for r in rolls), dtype=np.int64)
    w.atr_ord = {dt.date.fromisoformat(k).toordinal(): v for k, v in atr_by_day.items()}
    w.last_ord = dt.date.fromisoformat(last_day).toordinal()
    return w

def resample(w, step):
    b = w.T // step; starts = np.r_[0, np.flatnonzero(np.diff(b)) + 1]; ends = np.r_[starts[1:], len(b)]
    S = W(); S.o = w.O[starts]; S.c = w.C[ends - 1]; S.h = np.maximum.reduceat(w.H, starts); S.l = np.minimum.reduceat(w.L, starts)
    m = step // 60; S.key = (w.mins[starts] // m) * m; S.ord = w.ords[starts]; S.sess = S.ord + (S.key >= 1080); S.n = len(S.o)
    S.ok = (S.ord <= w.last_ord) & ~np.isin(S.sess, w.rollords)
    S.atrd = np.array([w.atr_ord.get(int(x), np.nan) for x in S.ord])
    tr = np.maximum(S.h - S.l, np.maximum(np.abs(S.h - np.r_[S.c[:1], S.c[:-1]]), np.abs(S.l - np.r_[S.c[:1], S.c[:-1]])))
    S.tr = tr; cs = np.r_[0, np.cumsum(tr)]; S.atrh = np.full(S.n, np.nan)
    if S.n > 15: S.atrh[15:] = (cs[14:S.n - 1] - cs[0:S.n - 15]) / 14   # mean of the 14 bars before bar i
    S.step = step
    return S

# ---------------------------------------------------------------- simulation
def sim(S, E, side, d, end, R, cost):
    """Net points per trade. side/d/end arrays, R target multiple or None. Stop wins a same-bar tie; gaps fill at the open."""
    E = np.asarray(E); side = np.asarray(side, dtype=float); d = np.asarray(d, dtype=float); end = np.asarray(end)
    K = int((end - E).max()) + 1; k = np.arange(K)[None, :]; raw = E[:, None] + k; valid = raw <= end[:, None]
    idx = np.minimum(raw, S.n - 1); s = side[:, None]
    o = S.o[idx] * s; hi = np.where(s > 0, S.h[idx], -S.l[idx]); lo = np.where(s > 0, S.l[idx], -S.h[idx])
    e = (S.o[E] * side)[:, None]; stop = e - d[:, None]
    hs = (lo <= stop) & valid; sfill = np.minimum(stop, o)
    r = np.arange(len(E))
    if R is not None:
        tgt = e + R * d[:, None]; ht = (hi >= tgt) & valid; tfill = np.maximum(tgt, o); ev = hs | ht
    else:
        ht = None; ev = hs
    has = ev.any(1); first = ev.argmax(1); hit_s = hs[r, first]
    last = S.c[end] * side
    if R is not None: fill = np.where(hit_s, sfill[r, first], tfill[r, first])
    else: fill = sfill[r, first]
    exitp = np.where(has, fill, last)
    return exitp - e[:, 0] - cost

def trades_dict(S, E, side, end, dk=None, d=None, R=None, arr='atrd'):
    E = np.asarray(E, dtype=np.int64)
    t = dict(E=E, side=np.asarray(side, dtype=float), end=np.asarray(end, dtype=np.int64), R=R, arr=arr, key=S.key[E])
    if dk is not None: t['d'] = dk * getattr(S, arr)[E]; t['dk'] = dk
    else: t['d'] = np.asarray(d, dtype=float); t['dk'] = None
    good = np.isfinite(t['d']) & (t['d'] > 0) & S.ok[E] & S.ok[t['end']] & (t['end'] >= E)
    for k in ('E', 'side', 'end', 'd', 'key'): t[k] = t[k][good]
    return t

# ---------------------------------------------------------------- random opponents
def build_pool(S, hold, daily_close):
    """key -> (entry idx, end idx) over every allowed bar."""
    n = S.n; pool = {}
    if daily_close:
        close = {}
        for i in np.flatnonzero((S.key == 955)): close[int(S.ord[i])] = i
        ends = np.array([close.get(int(o), -1) for o in S.ord]); idx = np.flatnonzero((ends >= 0) & (np.arange(n) < ends) & (S.key >= 570) & (S.key < 955))
        ends = ends[idx]
    else:
        idx = np.arange(0, n - hold); ends = idx + hold - 1
    m = S.ok[idx] & S.ok[ends]; idx, ends = idx[m], ends[m]
    for kk in np.unique(S.key[idx]):
        mm = S.key[idx] == kk; pool[int(kk)] = (idx[mm], ends[mm])
    return pool

def baseline(S, t, mode, pool, cost, rng):
    n = len(t['E']); out = np.empty(SIMS)
    for c0 in range(0, SIMS, CHUNK):
        cs = min(CHUNK, SIMS - c0); Rm = np.full((n, cs), np.nan)
        if mode == 'coin':
            sides = rng.choice([-1.0, 1.0], size=(n, cs)).ravel(); E = np.repeat(t['E'], cs); end = np.repeat(t['end'], cs); d = np.repeat(t['d'], cs)
            p = sim(S, E, sides, d, end, t['R'], cost); Rm = (p / d).reshape(n, cs)
        else:
            for kk in np.unique(t['key']):
                rows = np.flatnonzero(t['key'] == kk); PE, PEND = pool.get(int(kk), (None, None))
                if PE is None or len(PE) == 0: continue
                sel = rng.integers(0, len(PE), size=(len(rows), cs)); Er = PE[sel].ravel(); endr = PEND[sel].ravel()
                sd = np.repeat(t['side'][rows], cs)
                dr = (t['dk'] * getattr(S, t['arr'])[Er]) if t['dk'] is not None else np.repeat(t['d'][rows], cs)
                okd = np.isfinite(dr) & (dr > 0); res = np.full(len(Er), np.nan)
                if okd.any(): res[okd] = sim(S, Er[okd], sd[okd], dr[okd], endr[okd], t['R'], cost) / dr[okd]
                Rm[rows] = res.reshape(len(rows), cs)
        out[c0:c0 + cs] = np.nanmean(Rm, axis=0)
    return out

def summarize(S, t, cost, mode=None, pool=None, rng=None):
    if len(t['E']) < 30: return dict(n=int(len(t['E'])), note='too few trades')
    p = sim(S, t['E'], t['side'], t['d'], t['end'], t['R'], cost); R = p / t['d']; h = len(R) // 2
    o = dict(n=int(len(R)), win_pct=round(float((p > 0).mean() * 100), 1), mean_R=round(float(R.mean()), 4), net_pts_per_trade=round(float(p.mean()), 2),
             total_R=round(float(R.sum()), 1), half1_R=round(float(R[:h].mean()), 4), half2_R=round(float(R[h:].mean()), 4))
    if mode:
        b = baseline(S, t, mode, pool, cost, rng)
        o.update(random_mean_R=round(float(np.nanmean(b)), 4), beats_random_pct=round(float((b < R.mean()).mean() * 100), 1), baseline=mode)
    return o

# ---------------------------------------------------------------- signals
def ema(x, n):
    a = 2 / (n + 1); out = np.empty(len(x)); v = x[0]
    for i, y in enumerate(x): v = a * y + (1 - a) * v; out[i] = v
    return out

def hourly_signals(S):
    """name -> (list of signal bar idx, side array, hold). Entry is the next bar's open."""
    c = S.c; n = S.n; res = {}
    e20, e50 = ema(c, 20), ema(c, 50); sg = np.sign(e20 - e50); ix = [i for i in range(51, n) if sg[i] != 0 and sg[i - 1] != 0 and sg[i] != sg[i - 1]]
    res['ema_cross'] = (ix, [sg[i] for i in ix], 4)
    macd = ema(c, 12) - ema(c, 26); sig = ema(macd, 9); df = np.sign(macd - sig); ix = [i for i in range(40, n) if df[i] != 0 and df[i - 1] != 0 and df[i] != df[i - 1]]
    res['macd_cross'] = (ix, [df[i] for i in ix], 4)
    # SuperTrend (10, 3)
    atr10 = np.full(n, np.nan); cs = np.r_[0, np.cumsum(S.tr)]; atr10[10:] = (cs[11:] - cs[1:n - 9]) / 10
    hl2 = (S.h + S.l) / 2; ub = hl2 + 3 * atr10; lb = hl2 - 3 * atr10; fu = ub.copy(); fl = lb.copy(); dr = np.zeros(n); dr[:11] = 1
    for i in range(11, n):
        fu[i] = ub[i] if (ub[i] < fu[i - 1] or c[i - 1] > fu[i - 1]) else fu[i - 1]
        fl[i] = lb[i] if (lb[i] > fl[i - 1] or c[i - 1] < fl[i - 1]) else fl[i - 1]
        if dr[i - 1] == 1: dr[i] = -1 if c[i] < fl[i] else 1
        else: dr[i] = 1 if c[i] > fu[i] else -1
    ix = [i for i in range(12, n) if dr[i] != dr[i - 1]]; res['supertrend'] = (ix, [dr[i] for i in ix], 4)
    # Bollinger squeeze breakout
    cs2 = np.r_[0, np.cumsum(c)]; cq = np.r_[0, np.cumsum(c * c)]; m = np.full(n, np.nan); sd = np.full(n, np.nan)
    m[19:] = (cs2[20:] - cs2[:n - 19]) / 20; var = (cq[20:] - cq[:n - 19]) / 20 - m[19:] ** 2; sd[19:] = np.sqrt(np.maximum(var, 0))
    bw = 4 * sd / m; up = m + 2 * sd; lw = m - 2 * sd; ix = []; sd_ = []
    for i in range(125, n):
        win = bw[i - 101:i - 1]
        if np.isnan(bw[i - 1]) or np.isnan(win).any(): continue
        if bw[i - 1] > np.percentile(win, 20): continue
        if c[i] > up[i] and c[i - 1] <= up[i - 1]: ix.append(i); sd_.append(1.0)
        elif c[i] < lw[i] and c[i - 1] >= lw[i - 1]: ix.append(i); sd_.append(-1.0)
    res['bb_squeeze'] = (ix, sd_, 2)
    return res

def fvg_trades(S):
    n = S.n; E = []; side = []; d = []; end = []
    for i in range(2, n - 2):
        a = S.atrh[i]
        if not np.isfinite(a): continue
        for sd_ in (1, -1):
            if sd_ == 1 and S.l[i] > S.h[i - 2]: top, bot = S.l[i], S.h[i - 2]
            elif sd_ == -1 and S.h[i] < S.l[i - 2]: top, bot = S.l[i - 2], S.h[i]   # top = far edge for shorts
            else: continue
            if top - bot < 0.2 * a: continue
            for j in range(i + 1, min(n - 2, i + 25)):
                touched = S.l[j] <= top if sd_ == 1 else S.h[j] >= bot
                if touched:
                    e = j + 1
                    ent = S.o[e]; dist = (ent - bot) if sd_ == 1 else (top - ent)
                    if dist >= 0.25 * a and e + 48 < n and ((sd_ == 1 and ent > bot) or (sd_ == -1 and ent < top)):
                        E.append(e); side.append(sd_); d.append(dist); end.append(min(n - 1, e + 47))
                    break
    return E, side, d, end

# ---------------------------------------------------------------- one market
def day_index(S5):
    idx = {k: {} for k in (570, 575, 955)}
    for i in np.flatnonzero(np.isin(S5.key, (570, 575, 955)) & S5.ok): idx[int(S5.key[i])][int(S5.ord[i])] = i
    return idx

def market(sym, w, D, dl, cost, rng):
    out = {}; S5 = resample(w, 300); S60 = resample(w, 3600)
    ix = day_index(S5); E = []; end = []; sd_open = []; sd_dir = []; ords = []
    ema12 = ema(S5.c, 12)
    pool5 = build_pool(S5, None, True)
    for o, i0 in ix[570].items():
        i1 = ix[575].get(o); ie = ix[955].get(o)
        if i1 is None or ie is None or i1 != i0 + 1 or ie - i1 != 76: continue
        E.append(i1); end.append(ie); sd_open.append(1.0 if S5.c[i0] > S5.o[i0] else -1.0 if S5.c[i0] < S5.o[i0] else 0.0)
        sd_dir.append(1.0 if S5.c[i0] > ema12[i0] else -1.0 if S5.c[i0] < ema12[i0] else 0.0); ords.append(o)
    E = np.array(E); end = np.array(end); sd_open = np.array(sd_open); sd_dir = np.array(sd_dir)
    def mk(side, name, mode):
        m = side != 0; t = trades_dict(S5, E[m], side[m], end[m], dk=0.5, arr='atrd')
        out[name] = summarize(S5, t, cost, mode, pool5, rng); print(sym, name, out[name], flush=True)
    mk(sd_dir, 'candle_momentum_ema12', 'coin'); mk(sd_open, 'first_candle_direction', 'coin')
    mk(np.ones(len(E)), 'always_long', None); mk(-np.ones(len(E)), 'always_short', None)
    # Larry Williams range break
    rows = []; ordinal = {dt.date.fromisoformat(d_).toordinal(): d_ for d_ in dl}; dls = sorted(ordinal)
    for k, o in enumerate(dls):
        if k == 0 or o not in ix[570]: continue
        pv = D[ordinal[dls[k - 1]]]; dd = D[ordinal[o]]; pr = pv['h'] - pv['l']
        if pr <= 0 or o not in ix[955]: continue
        i0 = ix[570][o]; ie = ix[955][o]; up = dd['o'] + 0.5 * pr; dn = dd['o'] - 0.5 * pr
        for j in range(i0, ie - 1):
            hu = S5.h[j] >= up; hd = S5.l[j] <= dn
            if hu and hd: break
            if hu or hd: rows.append((j + 1, 1.0 if hu else -1.0, ie, 0.5 * pr)); break
    if rows:
        t = trades_dict(S5, [r[0] for r in rows], [r[1] for r in rows], [r[2] for r in rows], d=[r[3] for r in rows])
        out['larry_williams_break'] = summarize(S5, t, cost, 'time', pool5, rng); print(sym, 'larry_williams_break', out['larry_williams_break'], flush=True)
    # hourly rules
    sigs = hourly_signals(S60)
    for name, (ix_, sides, hold) in sigs.items():
        pool = build_pool(S60, hold, False); Ee = np.array(ix_, dtype=np.int64) + 1; m = Ee + hold - 1 < S60.n
        t = trades_dict(S60, Ee[m], np.array(sides)[m], Ee[m] + hold - 1, dk=1.5, arr='atrh')
        out[name] = summarize(S60, t, cost, 'time', pool, rng); print(sym, name, out[name], flush=True)
    E_, s_, d_, e_ = fvg_trades(S60)
    if E_:
        poolf = build_pool(S60, 48, False); t = trades_dict(S60, E_, s_, e_, d=d_, R=2.0)
        out['fair_value_gap'] = summarize(S60, t, cost, 'time', poolf, rng); print(sym, 'fair_value_gap', out['fair_value_gap'], flush=True)
    return out

def fed_and_po3(sym, c, w, D, dl):
    out = {}; fomc = sorted(c.FOMC); ret = []
    for d_ in fomc:
        if d_ in D and d_ <= c.LAST_DAY:
            k = dl.index(d_)
            if k > 0 and dl[k - 1] in D: ret.append(D[d_]['c'] / D[dl[k - 1]]['c'] - 1)
    allr = np.array([D[dl[k]]['c'] / D[dl[k - 1]]['c'] - 1 for k in range(1, len(dl)) if dl[k] <= c.LAST_DAY])
    if len(ret) >= 15:
        r = np.array(ret) - c.COST[sym] / np.mean([D[x]['c'] for x in dl]); rng = np.random.default_rng(40)
        b = np.array([rng.choice(allr, len(r)).mean() for _ in range(SIMS)])
        out['fed_day_drift'] = dict(n=len(r), mean_pct=round(float(r.mean() * 100), 3), all_days_mean_pct=round(float(allr.mean() * 100), 3), win_pct=round(float((r > 0).mean() * 100), 1),
                                    beats_random_pct=round(float((b < r.mean()).mean() * 100), 1))
    return out

def power3(w, D, dl, last_day):
    mm = w.mins; ords = w.ords; res = collections.defaultdict(list)
    first = {}
    for i in np.flatnonzero(mm == 0): first.setdefault(int(ords[i]), i)
    ordinal = {dt.date.fromisoformat(d_).toordinal(): d_ for d_ in dl}; lo = dt.date.fromisoformat(last_day).toordinal()
    dip = []; allc = []
    for o, i0 in first.items():
        if o > lo or o not in ordinal: continue
        seg = w.L[i0:i0 + 180];
        if len(seg) < 180: continue
        op = w.O[i0]; closed_up = D[ordinal[o]]['c'] > op; dipped = seg.min() < op
        allc.append(closed_up)
        if dipped: dip.append(closed_up)
    if not allc: return {}
    return dict(days=len(allc), dip_rate_pct=round(100 * len(dip) / len(allc), 1), close_up_after_dip_pct=round(100 * float(np.mean(dip)), 1) if dip else None, close_up_all_days_pct=round(100 * float(np.mean(allc)), 1))

def main():
    import common as c
    out = dict(era=c.DATA, last_day=c.LAST_DAY, sims=SIMS, markets={})
    for sym in ('NQ', 'ES'):
        T, O, H, L, C, n, mins, days, wd = c.prep(sym); D, dl, atr = c.daily(sym); R = c.roll(sym)
        w = make_world(T, O, H, L, C, mins, days, R | set(c.bad_days(sym)), atr, c.LAST_DAY)
        rng = np.random.default_rng(40 + (sym == 'ES'))
        out['markets'][sym] = market(sym, w, D, dl, c.COST[sym], rng)
        if sym == 'NQ':
            out['markets'][sym].update(fed_and_po3(sym, c, w, D, dl)); out['markets'][sym]['power_of_three'] = power3(w, D, dl, c.LAST_DAY)
            print('NQ extras', {k: out['markets'][sym][k] for k in ('fed_day_drift', 'power_of_three') if k in out['markets'][sym]}, flush=True)
    json.dump(out, open(f'{A}/batch40_{c.DATA}.json', 'w'), indent=1)

if __name__ == '__main__': main()
