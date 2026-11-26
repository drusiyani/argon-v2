"""Argon-1 data rules on synthetic bars (no real data needed)."""
import os, sys, datetime as dt
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'research'))
from argon1 import data as A


def fake_minutes(days=60, seed=1, switch_day=30, start='2021-03-01'):
    rng = np.random.default_rng(seed); rows = []; px = 13000.0; iid = 1
    d0 = dt.date.fromisoformat(start)
    ny = 'America/New_York'
    for k in range(days + 5):
        d = d0 + dt.timedelta(days=k)
        if d.weekday() >= 5: continue
        if k == switch_day: iid = 2; px *= 1.01          # roll: new contract trades 1% higher
        start_t = pd.Timestamp(dt.datetime.combine(d - dt.timedelta(days=1), dt.time(18)), tz=ny)
        for m in range(23 * 60):                            # 18:00 -> 17:00
            t = start_t + pd.Timedelta(minutes=m)
            o = px; px *= math_exp(rng.normal(0, 0.0004)); h = max(o, px) * 1.0001; l = min(o, px) * 0.9999
            rows.append((t.tz_convert('UTC').strftime('%Y-%m-%dT%H:%M:%S.000000000Z'), o, h, l, px, 10.0, iid))
    return pd.DataFrame(rows, columns=['ts_event', 'open', 'high', 'low', 'close', 'volume', 'instrument_id'])


def math_exp(x): return float(np.exp(x))


def to_bars(df):
    m = df.copy(); m['ts'] = pd.to_datetime(m['ts_event'].str[:19], utc=True)
    return A.five_minute(m[['ts', 'open', 'high', 'low', 'close', 'volume', 'instrument_id']])


def vix_for(dates):
    return {d: 15.0 + (i % 7) for i, d in enumerate(sorted(dates))}


def setup():
    nq = to_bars(fake_minutes(seed=1)); es = to_bars(fake_minutes(seed=2))
    v = vix_for(set(nq['sd']) | {(dt.date.fromisoformat(min(nq['sd'])) - dt.timedelta(days=k)).isoformat() for k in range(1, 30)})
    return nq, es, v


def test_label_and_shapes():
    nq, es, v = setup()
    D = A.build({'NQ': nq, 'ES': es}, v, fomc=set())
    assert len(D['dates']) > 10 and D['seq'].shape[1:] == (2, A.SEQ, 4) and D['ctx'].shape[1] == len(A.CTX_FEATS)
    r = A.rth_summary(nq)
    for d, y in zip(D['dates'], D['y']):
        R = r[d]; assert y == (1.0 if abs(R['c'] - R['o']) >= 0.6 * (R['h'] - R['l']) else 0.0)


def test_no_peeking_after_0845():
    nq, es, v = setup()
    D1 = A.build({'NQ': nq, 'ES': es}, v, fomc=set())
    d = D1['dates'][-3]
    nq2 = nq.copy(); late = (nq2['sd'] == d) & (nq2['mins'] >= A.CUT) & (nq2['mins'] < 18 * 60)
    nq2.loc[late, ['open', 'high', 'low', 'close']] *= 1.05; nq2.loc[late, 'volume'] *= 9
    D2 = A.build({'NQ': nq2, 'ES': es}, v, fomc=set())
    i = list(D1['dates']).index(d)
    assert np.array_equal(D1['seq'][i], D2['seq'][i]) and np.array_equal(D1['ctx'][i], D2['ctx'][i])


def test_roll_is_not_a_move():
    m = fake_minutes(seed=3); m['ts'] = pd.to_datetime(m['ts_event'].str[:19], utc=True)
    c = A.chain(m[['ts', 'open', 'high', 'low', 'close', 'volume', 'instrument_id']])
    r = np.abs(np.log(c['close'] / c['close'].shift()).dropna())
    assert r.max() < 0.005          # the raw 1% jump at the switch is gone


def test_chart_uses_ledger_trades_for_booked_days():
    """26 Nov 2026: the chart showed 'No trades' for a booked day. Booked days must take the ledger's trades."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    s = open(os.path.join(root, 'engine', 'site_template.html')).read()
    assert "data('live_days')" in s and 'S.trades=v.t' in s
