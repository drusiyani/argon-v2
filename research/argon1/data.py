"""Argon-1 data: 5-minute bars, the trend-day label and the inputs known at 08:45 New York.

Runs only on GitHub Actions with the private Databento data (data/lockbox2010 for 2011-2020, data/databento for 2021+),
or on synthetic bars in the tests. Uses NQ and ES only: the 2011-2020 data has nothing else.

Rules (fixed in research/ARGON1_PLAN.md and Amendment 15):
- label: trend day = |close - open| >= 0.6 x (high - low), NQ 09:30-16:00 New York; short RTH sessions are not scored.
- inputs: only bars that START before 08:45 New York on the day (the 08:40 bar is the last one), plus the VIX close of
  the previous trading day.
- continuous contract: when the contract switches, that bar's return is set to zero (prices are ratio-chained), so a
  roll never looks like a market move.
"""
import os, glob, gzip, math, datetime as dt
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SYMS = ('NQ', 'ES')
CUT = 8 * 60 + 45            # 08:45: last usable bar starts at 08:40
SEQ = 256                    # bars of history fed to the models (about 21 hours)
RTH0, RTH1 = 9 * 60 + 30, 16 * 60
FULL_RTH_BARS = 78
SEQ_FEATS = ('ret', 'hl', 'co', 'vol')
CTX_FEATS = ('on_nq', 'on_es', 'on_range', 'prev_ret', 'prev_trend', 'range_ratio', 'rsi5', 'ret5',
             'vix', 'vix_pct', 'fomc', 'opex', 'jobs', 'mon', 'tue', 'wed', 'thu', 'fri')


# ------------------------------------------------------------------ loading
def read_minutes(sym, folders=('lockbox2010', 'databento')):
    """All 1-minute rows for a symbol from the given data folders, newest file wins on duplicates."""
    parts = []
    for fo in folders:
        for f in sorted(glob.glob(os.path.join(ROOT, 'data', fo, f'{sym}_*.csv.gz'))):
            if os.path.getsize(f) == 0: continue
            d = pd.read_csv(f, usecols=lambda c: c in ('ts_event', 'open', 'high', 'low', 'close', 'volume', 'instrument_id'))
            parts.append(d)
    if not parts: raise FileNotFoundError(f'no data for {sym}')
    m = pd.concat(parts, ignore_index=True)
    m['ts'] = pd.to_datetime(m['ts_event'].str[:19], utc=True)
    m = m.drop_duplicates('ts', keep='last').sort_values('ts').reset_index(drop=True)
    if 'instrument_id' not in m: m['instrument_id'] = 0
    if 'volume' not in m: m['volume'] = 0.0
    return m[['ts', 'open', 'high', 'low', 'close', 'volume', 'instrument_id']]


def chain(m):
    """Ratio-chain prices across contract switches so the switch bar has zero return."""
    m = m.copy()
    sw = (m['instrument_id'] != m['instrument_id'].shift()).to_numpy().copy(); sw[0] = False
    ratio = np.ones(len(m))
    prev_close = m['close'].shift().to_numpy().copy()
    ratio[sw] = prev_close[sw] / m['open'].to_numpy()[sw]
    f = np.cumprod(ratio)
    for c in ('open', 'high', 'low', 'close'): m[c] = m[c] * f
    return m


def five_minute(m):
    """1-minute rows -> 5-minute bars with New York time, session date (18:00 starts the next session) and minute of day."""
    m = chain(m)
    k = m['ts'].dt.floor('5min')
    b = m.groupby(k).agg(open=('open', 'first'), high=('high', 'max'), low=('low', 'min'), close=('close', 'last'),
                         volume=('volume', 'sum')).reset_index().rename(columns={'ts': 't'})
    ny = b['t'].dt.tz_convert('America/New_York')
    b['mins'] = ny.dt.hour * 60 + ny.dt.minute
    d = ny.dt.date
    b['sd'] = [x + dt.timedelta(days=1) if h >= 18 else x for x, h in zip(d, ny.dt.hour)]
    b = b[[s.weekday() < 5 for s in b['sd']]].reset_index(drop=True)
    b['sd'] = [s.isoformat() for s in b['sd']]
    return b


# ------------------------------------------------------------------ calendar
def fomc_days():
    import sys; sys.path.insert(0, os.path.join(ROOT, 'engine')); sys.path.insert(0, os.path.join(ROOT, 'research'))
    from calendar_us import FOMC; from calendar_hist import FOMC_HIST
    return set(FOMC) | set(FOMC_HIST)


def opex(d):   # third Friday of the month
    x = dt.date.fromisoformat(d); return x.weekday() == 4 and 15 <= x.day <= 21


def jobs_friday(d):   # first Friday of the month (the usual jobs-report day)
    x = dt.date.fromisoformat(d); return x.weekday() == 4 and x.day <= 7


def rsi(closes, n=5):
    g = [max(0, b - a) for a, b in zip(closes, closes[1:])][-n:]; l = [max(0, a - b) for a, b in zip(closes, closes[1:])][-n:]
    return 100.0 if sum(l) == 0 else 100 - 100 / (1 + (sum(g) / n) / (sum(l) / n))


# ------------------------------------------------------------------ per-day records
def rth_summary(b):
    """{session: dict(o,h,l,c,n)} for 09:30-16:00 New York."""
    r = b[(b['mins'] >= RTH0) & (b['mins'] < RTH1)]
    g = r.groupby('sd').agg(o=('open', 'first'), h=('high', 'max'), l=('low', 'min'), c=('close', 'last'), n=('open', 'size'))
    return {k: v for k, v in g.to_dict('index').items()}


def seq_block(b, end_idx):
    """The SEQ bars ending at end_idx (inclusive) as a (SEQ, 4) array: log return %, log(high/low) %, log(close/open) %,
    log volume minus its window median. Left-padded with zeros if history is short."""
    lo = max(0, end_idx - SEQ + 1)
    w = b.iloc[lo:end_idx + 1]
    c = w['close'].to_numpy(); o = w['open'].to_numpy(); h = w['high'].to_numpy(); l = w['low'].to_numpy()
    prev = np.concatenate([[o[0]], c[:-1]])
    ret = np.log(c / prev) * 100; hl = np.log(h / l) * 100; co = np.log(c / o) * 100
    lv = np.log1p(w['volume'].to_numpy()); vol = lv - np.median(lv)
    x = np.stack([ret, hl, co, vol], 1).astype(np.float32)
    x = np.clip(x, -10, 10)
    if len(x) < SEQ: x = np.concatenate([np.zeros((SEQ - len(x), 4), np.float32), x])
    return x


def raw_block(b, end_idx):
    """The SEQ bars ending at end_idx as Kronos wants them: (SEQ, 6) open, high, low, close, volume, amount and (SEQ, 5)
    time stamps (minute, hour, weekday, day, month, New York). Left-padded by repeating the first bar."""
    lo = max(0, end_idx - SEQ + 1); w = b.iloc[lo:end_idx + 1]
    px = w[['open', 'high', 'low', 'close', 'volume']].to_numpy(np.float64)
    amt = (px[:, 3] * px[:, 4])[:, None]
    x = np.concatenate([px, amt], 1).astype(np.float32)
    ny = w['t'].dt.tz_convert('America/New_York')
    st = np.stack([ny.dt.minute, ny.dt.hour, ny.dt.weekday, ny.dt.day, ny.dt.month], 1).astype(np.float32)
    if len(x) < SEQ:
        k = SEQ - len(x); x = np.concatenate([np.repeat(x[:1], k, 0), x]); st = np.concatenate([np.repeat(st[:1], k, 0), st])
    return x, st


def build(bars, vix, fomc=None, first=None, last=None, today=None):
    """bars: {'NQ': 5m frame, 'ES': 5m frame}; vix: {iso date: close}.
    Returns dict(dates, seq (N,2,SEQ,4), ctx (N,len(CTX_FEATS)), y (N,), ok (N,) label usable).
    today: a session with no regular-hours bars yet (the live 08:45 call); its label is NaN."""
    fomc = fomc_days() if fomc is None else fomc
    rth = {s: rth_summary(bars[s]) for s in SYMS}
    sessions = sorted(set(rth['NQ']) & set(rth['ES']))
    if today and today not in sessions: sessions = sorted(sessions + [today])
    vk = sorted(vix)
    out = dict(dates=[], seq=[], ctx=[], y=[], ok=[], raw=[], stamp=[])
    idx = {s: bars[s].reset_index(drop=True) for s in SYMS}
    # position of the last bar before 08:45 of each session
    cutpos = {}
    for s in SYMS:
        b = idx[s]; sub = b[b['mins'] < CUT]
        cutpos[s] = pd.Series(sub.index, index=sub['sd']).groupby(level=0).last().to_dict()
    b = idx['NQ']; nm = b[(b['mins'] < CUT) | (b['mins'] >= 18 * 60)]
    night = nm.groupby('sd').agg(h=('high', 'max'), l=('low', 'min')).to_dict('index')
    for i, d in enumerate(sessions):
        if i < 21: continue
        if first and d < first: continue
        if last and d > last: continue
        if not all(d in cutpos[s] for s in SYMS): continue
        prev = sessions[i - 1]; hist = sessions[i - 21:i]
        R = rth['NQ'].get(d); P = rth['NQ'][prev]
        ok = R is not None and R['n'] >= FULL_RTH_BARS - 3 and P['n'] >= FULL_RTH_BARS - 3
        y = float('nan') if R is None else (1.0 if abs(R['c'] - R['o']) >= 0.6 * (R['h'] - R['l']) else 0.0)
        seqs = []; on = {}; raws = []; sts = []
        for s in SYMS:
            j = cutpos[s][d]; b = idx[s]
            seqs.append(seq_block(b, j)); rx, st = raw_block(b, j); raws.append(rx); sts.append(st)
            on[s] = (b['close'].iat[j] / rth[s][prev]['c'] - 1) * 100
        prng = P['h'] - P['l']
        rngs = [rth['NQ'][x]['h'] - rth['NQ'][x]['l'] for x in hist[-20:]]
        closes = [rth['NQ'][x]['c'] for x in hist]
        v_prev = [v for v in vk if v < d]
        vx = vix[v_prev[-1]] if v_prev else float('nan')
        win = [vix[v] for v in v_prev[-252:]]
        vp = sum(1 for v in win if v <= vx) / len(win) if win else float('nan')
        wd = dt.date.fromisoformat(d).weekday()
        ctx = [on['NQ'], on['ES'], (night[d]['h'] - night[d]['l']) / prng if prng else 0,
               (P['c'] / P['o'] - 1) * 100, abs(P['c'] - P['o']) / prng if prng else 0,
               prng / (sum(rngs) / len(rngs)), rsi(closes, 5), (closes[-1] / closes[-6] - 1) * 100,
               vx, vp, float(d in fomc), float(opex(d)), float(jobs_friday(d))] + [float(wd == k) for k in range(5)]
        if any(isinstance(v, float) and math.isnan(v) for v in ctx): continue
        if d not in night: continue
        out['dates'].append(d); out['seq'].append(np.stack(seqs)); out['ctx'].append(np.array(ctx, np.float32))
        out['y'].append(y); out['ok'].append(ok); out['raw'].append(np.stack(raws)); out['stamp'].append(np.stack(sts))
    return dict(dates=np.array(out['dates']), seq=np.stack(out['seq']) if out['seq'] else np.zeros((0, 2, SEQ, 4), np.float32),
                ctx=np.stack(out['ctx']) if out['ctx'] else np.zeros((0, len(CTX_FEATS)), np.float32),
                y=np.array(out['y'], np.float32), ok=np.array(out['ok'], bool),
                raw=np.stack(out['raw']) if out['raw'] else np.zeros((0, 2, SEQ, 6), np.float32),
                stamp=np.stack(out['stamp']) if out['stamp'] else np.zeros((0, 2, SEQ, 5), np.float32))


def vix_history():
    """VIX daily closes from FRED (VIXCLS), fetched on the runner."""
    import urllib.request, io
    raw = urllib.request.urlopen('https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS', timeout=60).read().decode()
    d = pd.read_csv(io.StringIO(raw)); d.columns = ['date', 'v']
    d = d[pd.to_numeric(d['v'], errors='coerce').notna()]
    return {r.date: float(r.v) for r in d.itertuples()}
