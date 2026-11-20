"""The plain package's Nasdaq core for the live book (Amendment 13), ported from analysis/batch14_dump.py build().

Each booked day from the switch date on, the book also holds micro Nasdaq futures (MNQ) from the previous session's close
to this session's close, sized to `w` x the account:
  w = min(1.5, median of VXN over the past year / latest VXN)   (VXN known before yesterday's close, as in the research)
  contracts = the NEAREST whole MNQ (rounding down would hold about half the target on a $100k account; Amendment 13)
Plus, on Fed decision days, a second 1x holding from the previous close to 13:59 New York (the pre-FOMC leg, with costs),
and interest on the account at the 3-month T-bill rate (FRED DTB3).
Roll days use open to close, as the research does; days flagged as bad data earn nothing.

The inputs for each day (VXN used, its median, w, the T-bill rate) are worked out once, when the day is first booked, and
saved in core_inputs.json next to the ledger. Replays read them back, so a later data revision can never change a booked day."""
import os, csv, bisect, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PPT = 2.0                      # MNQ dollars per index point
FOMC_EXIT = 839                # 13:59 New York (minutes after midnight); the research's exit for every meeting since 2013
STALE_DAYS = 10                # if the newest VXN print is older than this, the core runs at w = 1 that day (logged)

def _csv(fn, col):
    out = {}
    p = os.path.join(ROOT, 'analysis', fn)
    if not os.path.exists(p): return out
    for r in csv.DictReader(open(p)):
        try: out[r['date']] = float(r[col])
        except (ValueError, KeyError): pass
    return out

def _lastbefore(src, keys, d):
    i = bisect.bisect_left(keys, d); return (src[keys[i - 1]], i - 1) if i > 0 else (None, -1)

def inputs(d, p):
    """The day's core inputs, from data known before the open (VXN before the previous session, T-bill before today)."""
    import datetime as dt
    V = _csv('vxn.csv', 'vxn'); vk = sorted(V); v, i = _lastbefore(V, vk, p)
    out = dict(vxn_date=vk[i] if v is not None else None, vxn=v, vxn_median=None, w=1.0, note='')
    if v is None: out['note'] = 'no VXN data: w = 1'
    elif (dt.date.fromisoformat(p) - dt.date.fromisoformat(vk[i])).days > STALE_DAYS: out['note'] = f'VXN stale (last {vk[i]}): w = 1'
    else:
        h = sorted(V[x] for x in vk[max(0, i - 251):i + 1]); med = h[len(h) // 2] if len(h) >= 60 else v
        out.update(vxn_median=med, w=round(min(1.5, med / v), 6))
    T = _csv('tbill_dtb3.csv', 'dtb3_pct'); tk = sorted(T); tb, j = _lastbefore(T, tk, d)
    out.update(tbill_pct=tb if tb is not None else 0.0, tbill_date=tk[j] if tb is not None else None)
    return out

def skipset(c, S='NQ'):
    out = {'roll': set(), 'bad': set()}
    for f, k in (('roll', 'roll'), ('bad_days', 'bad')):
        try:
            v = getattr(c, f)(S); v = v.keys() if isinstance(v, dict) else v; out[k] = {x for x in v if isinstance(x, str) and len(x) == 10}
        except Exception: pass
    return out

def nearest(x): return max(0, int(math.floor(x + 0.5)))

def day(c, d, inp, equity, cx):
    """The core's dollars for session d (previous session's close -> d's close), plus the FOMC leg and interest."""
    D, dl, _ = c.daily('NQ'); k = dl.index(d); p = dl[k - 1]; sk = skipset(c)
    prev = D[p]['c']; r = D[d]['c'] / prev - 1
    bad = d in sk['bad'] or p in sk['bad']; roll = d in sk['roll'] or p in sk['roll']
    if bad: pts, how = 0.0, 'bad-data day: no core result'
    elif roll or abs(r) > 0.15: pts, how = D[d]['c'] - D[d]['o'], 'roll day: open to close'
    else: pts, how = D[d]['c'] - prev, 'close to close'
    n = nearest(equity * inp['w'] / (prev * PPT))
    out = dict(contract='MNQ', contracts=n, weight=inp['w'], prev_session=p, from_price=round(prev, 2), to_price=round(D[d]['c'], 2),
               points=round(pts, 2), how=how, usd=round(n * PPT * pts, 2), inputs=inp)
    if d in c.FOMC and not bad:
        T, O, H, L, C, n_, mins, days, wd = c.prep('NQ'); i2 = [i for i in D[d]['r'] if mins[i] <= FOMC_EXIT]
        if i2:
            nf = nearest(equity / (prev * PPT)); fp = C[i2[-1]] - prev - cx * c.COST['NQ']
            out['fomc'] = dict(contracts=nf, exit_time='13:59', exit_price=round(C[i2[-1]], 2), points=round(fp, 2), usd=round(nf * PPT * fp, 2))
    out['interest_usd'] = round(equity * inp['tbill_pct'] / 100 / 252, 2)
    out['total_usd'] = round(out['usd'] + out.get('fomc', {}).get('usd', 0.0) + out['interest_usd'], 2)
    return out
