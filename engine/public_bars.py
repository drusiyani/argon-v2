"""Prices for the PUBLIC charts only (Chart tab, the desk's 'why it fired' sparklines).

Databento's licence forbids republishing CME data, so nothing drawn on the public site may come from it. These bars come
from Yahoo Finance instead (NQ=F / ES=F, the front contract, delayed). They are for looking at, not for trading: the
book, the ledger and every result are still computed from the private Databento data, so a candle here can sit a few
points away from the price the engine used.

Yahoo only serves about 60 sessions of 5-minute bars, so callers keep what they already published and add to it.
If Yahoo is down, callers get {} / [] back and keep the old file. They never fall back to Databento."""
import json, urllib.request, datetime as dt
from zoneinfo import ZoneInfo
NY = ZoneInfo('America/New_York')
YAHOO = {'NQ': 'NQ%3DF', 'ES': 'ES%3DF'}
SOURCE = 'Yahoo Finance (front contract, delayed). For display only: the engine uses private exchange data.'

def _get(sym, query):
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{YAHOO[sym]}?{query}'
    r = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read())['chart']['result'][0]
    q = r['indicators']['quote'][0]
    return [(t, o, h, l, c) for t, o, h, l, c in zip(r['timestamp'], q['open'], q['high'], q['low'], q['close']) if None not in (o, h, l, c)]

def daily(sym='NQ', start='2021-07-01'):
    """[[date, o, h, l, c], ...] daily candles from `start`. [] if Yahoo fails."""
    try:
        p1 = int(dt.datetime.fromisoformat(start).replace(tzinfo=NY).timestamp())
        rows = _get(sym, f'interval=1d&period1={p1}&period2=9999999999')
    except Exception as ex:
        print('public bars: Yahoo daily failed:', ex); return []
    out = {}
    for t, o, h, l, c in rows:
        d = dt.datetime.fromtimestamp(t, NY)
        if d.weekday() < 5: out[d.date().isoformat()] = [d.date().isoformat(), round(o, 2), round(h, 2), round(l, 2), round(c, 2)]
    return [out[d] for d in sorted(out) if d >= start]

def sessions(sym='NQ'):
    """{date: [[minute, o, h, l, c], ...]} 5-minute bars, 9:30-16:00 New York, for the ~60 sessions Yahoo has. {} if it fails."""
    try: rows = _get(sym, 'interval=5m&range=60d')
    except Exception as ex:
        print('public bars: Yahoo 5-minute failed:', ex); return {}
    out = {}
    for t, o, h, l, c in rows:
        d = dt.datetime.fromtimestamp(t, NY); m = d.hour * 60 + d.minute
        if d.weekday() < 5 and 570 <= m < 960: out.setdefault(d.date().isoformat(), []).append([m - m % 5, round(o, 2), round(h, 2), round(l, 2), round(c, 2)])
    return {d: b for d, b in out.items() if len(b) >= 30}      # a half-day or a broken download is not worth drawing
