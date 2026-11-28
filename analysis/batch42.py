"""Batch 42: trend sleeve, gold (GC) + 10-year Treasury (ZN), monthly 12-month momentum (rules: analysis/BATCH42_PREREG.md)."""
import os, sys, json, math, csv, gzip, bisect, random, statistics as stt, datetime as dt
A = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(A)
sys.path.insert(0, A); sys.path.insert(0, os.path.join(ROOT, 'research')); sys.path.insert(0, os.path.join(ROOT, 'engine'))
EXTRA = os.environ.get('B42_EXTRA', os.path.join(ROOT, 'data', 'extra'))
TICK = {'GC': 0.10, 'ZN': 1 / 64}; MULT = {'GC': 10.0, 'ZN': 1000.0}; TICKUSD = {'GC': 1.0, 'ZN': 15.625}   # whole-contract: MGC, ZN
VOL_T = 0.05; VOL_N = 60; LOOK_M = 12; ACCT = 100_000.0

def load(sym):
    """Daily bars {date: (close, instrument_id)}, Sunday/Saturday bars merged into the next weekday."""
    raw = {}
    with gzip.open(os.path.join(EXTRA, f'{sym}_daily.csv.gz'), 'rt') as f:
        for r in csv.DictReader(f):
            d = dt.date.fromisoformat(r['ts_event'][:10])
            raw.setdefault(d, []).append((float(r['close']), str(r['instrument_id'])))
    out = {}
    for d in sorted(raw):
        t = d
        while t.weekday() >= 5: t += dt.timedelta(days=1)
        out[t.isoformat()] = raw[d][-1]           # weekday close wins (it is processed after the weekend bar)
    return out

def market(sym, roll_ticks=1):
    """Per-day series for one market: date list, returns (roll day = 0), roll flags, closes."""
    B = load(sym); ds = sorted(B); ret = [0.0]; rolls = [False]; px = [B[ds[0]][0]]
    for k in range(1, len(ds)):
        (c1, i1), (c0, i0) = B[ds[k]], B[ds[k - 1]]
        rl = i1 != i0; rolls.append(rl); ret.append(0.0 if rl else c1 / c0 - 1); px.append(c1)
    return ds, ret, rolls, px

def sleeve_market(sym, roll_ticks=1):
    """Daily weighted returns after costs {date: r}, plus weights, rebalance count, and whole-contract $ P&L."""
    ds, ret, rolls, px = market(sym)
    # month ends: last bar of each calendar month
    me = [k for k in range(len(ds)) if k + 1 == len(ds) or ds[k + 1][:7] != ds[k][:7]]
    w_at = {}; n_at = {}
    for k in me:
        if k == len(ds) - 1: continue                      # no holding period after the last bar
        y, m = int(ds[k][:4]), int(ds[k][5:7]); ty, tm = (y - 1, m)
        prev = [j for j in me if ds[j][:7] == f'{ty:04d}-{tm:02d}']
        if not prev or k < VOL_N: continue
        j = prev[0]; g = 1.0
        for i in range(j + 1, k + 1): g *= 1 + ret[i]
        sig = 1 if g > 1 else -1 if g < 1 else 0
        win = ret[k - VOL_N + 1:k + 1]; vol = stt.pstdev(win) * math.sqrt(252)
        if not vol: continue
        w = sig * VOL_T / vol; w_at[k] = w
        n_at[k] = sig * int(math.floor(abs(w) * ACCT / (px[k] * MULT[sym]) + 0.5))
    out = {}; usd = {}; wts = {}; w = 0.0; n = 0; reb = 0; started = False
    for k in range(len(ds)):
        d = ds[k]
        r = w * ret[k] - (abs(w) * roll_ticks * TICK[sym] / px[k] if rolls[k] and w else 0.0)
        u = n * MULT[sym] * (px[k] - px[k - 1]) * (0 if rolls[k] else 1) - (abs(n) * roll_ticks * TICKUSD[sym] if rolls[k] else 0.0) if k else 0.0
        if k in w_at:                                      # rebalance at this close
            nw = w_at[k]; r -= abs(nw - w) * TICK[sym] / px[k]; u -= abs(n_at[k] - n) * TICKUSD[sym]
            if nw != w: reb += 1
            w = nw; n = n_at[k]; started = True
        if started or k in w_at: out[d] = r; usd[d] = u; wts[d] = w
    return out, usd, wts, reb

def on_sessions(series, sess):
    """Sum a GC/ZN-dated series into Nasdaq sessions: every day after the previous session up to and including d."""
    keys = sorted(series); res = []
    for i in range(1, len(sess)):
        lo = bisect.bisect_right(keys, sess[i - 1]); hi = bisect.bisect_right(keys, sess[i])
        res.append(sum(series[keys[j]] for j in range(lo, hi)))
    return res

def sr(x):
    sd = stt.pstdev(x); return round(stt.mean(x) / sd * math.sqrt(252), 3) if sd else 0.0

def corr(x, y):
    mx, my = stt.mean(x), stt.mean(y); sx, sy = stt.pstdev(x), stt.pstdev(y)
    return round(sum((a - mx) * (b - my) for a, b in zip(x, y)) / len(x) / (sx * sy), 3) if sx and sy else 0.0

def luck(book, idea, draws=2000, block=21, seed=42):
    rng = random.Random(seed); n = len(book); nb = math.ceil(n / block); worse = 0; gains = []
    for _ in range(draws):
        idx = []
        for _ in range(nb):
            s = rng.randrange(0, n - block + 1); idx.extend(range(s, s + block))
        idx = idx[:n]; b = [book[i] for i in idx]; bi = [book[i] + idea[i] for i in idx]
        g = sr(bi) - sr(b); gains.append(g); worse += g <= 0
    gains.sort()
    return dict(share_gain_le_0=round(worse / draws, 4), gain_p05=round(gains[int(0.05 * draws)], 3),
                gain_p50=round(gains[draws // 2], 3), draws=draws, block_days=block, seed=seed)

def main():
    import common as c
    from batch38 import rules_daily, stats
    ERA = c.DATA
    D, dl, _ = c.daily('NQ'); R = c.roll('NQ')
    V = {}
    for row in csv.DictReader(open(os.path.join(ROOT, 'analysis', 'vxn.csv'))):
        try: V[row['date']] = float(row['vxn'])
        except ValueError: pass
    vk = sorted(V); rd = rules_daily()
    days = []; core = []
    for k in range(260, len(dl)):
        d, p = dl[k], dl[k - 1]; roll = d in R or p in R
        i = bisect.bisect_left(vk, p)
        if i == 0: continue
        v = V[vk[i - 1]]; hist = sorted(V[x] for x in vk[max(0, i - 252):i]); w = min(1.5, hist[len(hist) // 2] / v)
        cc = (D[d]['c'] / D[d]['o'] - 1) if roll else (D[d]['c'] / D[p]['c'] - 1)
        if abs(cc) > 0.15: cc = 0.0
        days.append(d); core.append(w * cc)
    sess = [dl[dl.index(days[0]) - 1]] + days
    book = [cv + rd.get(d, 0.0) for cv, d in zip(core, days)]
    legs = {}; legs_usd = {}; reb = {}; legs2 = {}
    for s in ('GC', 'ZN'):
        x, u, wts, n = sleeve_market(s); legs[s] = on_sessions(x, sess); legs_usd[s] = on_sessions(u, sess); reb[s] = n
        legs2[s] = on_sessions(sleeve_market(s, roll_ticks=2)[0], sess)
    sleeve = [a + b for a, b in zip(legs['GC'], legs['ZN'])]
    sleeve2 = [a + b for a, b in zip(legs2['GC'], legs2['ZN'])]
    whole = [(a + b) / ACCT for a, b in zip(legs_usd['GC'], legs_usd['ZN'])]
    with_it = [a + b for a, b in zip(book, sleeve)]
    def year(x, y):
        g = 1.0
        for d, v in zip(days, x):
            if d[:4] == y: g *= 1 + v
        return round((g - 1) * 100, 2)
    sb, sw = stats(book), stats(with_it)
    out = dict(era=ERA, period=[days[0], days[-1]], sessions=len(days),
               book=sb, book_with_sleeve=sw, sharpe_gain=round(sw['sharpe'] - sb['sharpe'], 3),
               passes_this_era=sw['sharpe'] > sb['sharpe'],
               sleeve=dict(own_sharpe=sr(sleeve), gc_sharpe=sr(legs['GC']), zn_sharpe=sr(legs['ZN']),
                           ann_vol_pct=round(stt.pstdev(sleeve) * math.sqrt(252) * 100, 2),
                           corr_with_core=corr(sleeve, core), corr_with_book=corr(sleeve, book),
                           rebalances_with_change=reb, ret_2022_pct=year(sleeve, '2022'),
                           book_2022_pct=year(book, '2022'), book_with_2022_pct=year(with_it, '2022'),
                           yearly_pct={y: year(sleeve, y) for y in sorted({d[:4] for d in days})}),
               luck=luck(book, sleeve),
               info_only=dict(whole_contract=dict(own_sharpe=sr(whole), book_with_it=stats([a + b for a, b in zip(book, whole)])),
                              roll_cost_2_ticks=dict(own_sharpe=sr(sleeve2), book_with_it=stats([a + b for a, b in zip(book, sleeve2)]))),
               trial_count_approx=331)
    json.dump(out, open(f'{A}/batch42_{ERA}.json', 'w'), indent=1); print(json.dumps(out, indent=1))

if __name__ == '__main__': main()
