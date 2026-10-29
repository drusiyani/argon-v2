"""The desk's new job (Amendment 4): a morning DAY-TYPE forecast that sizes the v2 book, tested in the shadow first.

Every weekday between 8:45 and 9:25am New York, once:
  - collects what is knowable BEFORE the open: overnight move and range, yesterday's range vs its 20-day average, the 5-day
    RSI (the dealer-gamma clue from Zarattini et al.: strong rallies -> dealers long gamma -> intraday trends die faster),
    VIX and its 1-year percentile, today's calendar (FOMC, options expiry, jobs Friday) and the latest market headlines;
  - AI arm: asks the pinned model the same frozen question 3 times (temperature 0) and takes the MEDIAN size (0.5 / 1 / 1.5)
    and trend probability. It may veto the day only for a reason on the allowed list;
  - dumb-rule arm: yesterday's range / 20-day average range: above 1.2 -> 1.5x, below 0.8 -> 0.5x, else 1x;
  - writes one line to data/daytype.jsonl. Nothing here changes the real book: all three arms (1x, dumb rule, AI) are scored
    side by side by engine/daytype_score.py, and the AI only gets real control under the pre-registered promotion rule.
If the forecast is not finished by 9:25 the AI arm counts as 1x for that day (recorded as late)."""
import os, sys, json, time, hashlib, statistics as stt, urllib.request, datetime as dt, re, html
from zoneinfo import ZoneInfo
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'engine'))
from calendar_us import FOMC
NY = ZoneInfo('America/New_York'); OUT = os.path.join(ROOT, 'data', 'daytype.jsonl')
KEY = os.environ.get('ANTHROPIC_API_KEY'); MODEL = 'claude-sonnet-5-5'        # PINNED for the whole trial (changing it resets the clock)
SIZES = (0.5, 1.0, 1.5); VETOS = ('breaking_unscheduled_event', 'market_halt', 'data_feed_broken')
UA = {'User-Agent': 'Mozilla/5.0'}

PROMPT = """You are the morning forecaster on Argon's paper-trading desk. Argon runs four INTRADAY MOMENTUM strategies on Nasdaq-100
futures (plus one S&P 500 expiry trade). They make money on TREND days (big one-way moves after the open) and lose small amounts on
CHOP days (back-and-forth, mean-reverting). Your only job: before the 9:30 open, judge how likely today is to be a trend day, and
pick a size for the whole book: 0.5 (likely chop), 1 (normal) or 1.5 (likely trend). You do NOT pick direction.

What the research says (use it as a checklist):
- Momentum works best when volatility is high, on news and macro-release days, and when options dealers are short gamma (after selloffs).
- It works worst in calm markets: low VIX, small ranges, and after strong multi-day rallies (5-day RSI high -> dealers long gamma -> moves fade).
- Scheduled events (FOMC at 2pm, jobs reports, options expiry) change how a day trades. Overnight news is mostly priced in by the open;
  what matters is whether the day is likely to keep moving.

You may VETO the whole day (no trading) ONLY for one of these reasons: breaking_unscheduled_event (e.g. war, attack, emergency
central-bank action that is still unfolding), market_halt, data_feed_broken. Otherwise veto must be null.

Reply with ONLY this JSON, nothing else:
{"trend_probability": <0-100>, "size": <0.5|1|1.5>, "veto": <null or one allowed reason>, "reason": "<one or two sentences>"}

TODAY'S INPUTS:
"""
PROMPT_HASH = hashlib.sha256(PROMPT.encode()).hexdigest()[:16]

def get(url, timeout=20):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()

def chart(sym, rng, iv):
    r = json.loads(get(f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range={rng}&interval={iv}'))['chart']['result'][0]
    q = r['indicators']['quote'][0]
    return [(t, o, h, l, c) for t, o, h, l, c in zip(r['timestamp'], q['open'], q['high'], q['low'], q['close']) if None not in (o, h, l, c)]

def rsi(closes, n=5):
    g = [max(0, b - a) for a, b in zip(closes, closes[1:])][-n:]; l = [max(0, a - b) for a, b in zip(closes, closes[1:])][-n:]
    return 100.0 if sum(l) == 0 else round(100 - 100 / (1 + (sum(g) / n) / (sum(l) / n)), 1)

def inputs(today):
    """Only things known before 9:30 New York."""
    d = {}
    day = chart('NQ%3DF', '3mo', '1d')                                   # daily bars (the last one may be today's partial)
    done = [x for x in day if dt.datetime.fromtimestamp(x[0], NY).date() < today]
    rng = [h - l for _, o, h, l, c in done]; closes = [c for *_, c in done]
    d['yesterday_range_pts'] = round(rng[-1], 1); d['avg20_range_pts'] = round(stt.mean(rng[-20:]), 1)
    d['range_ratio'] = round(rng[-1] / stt.mean(rng[-20:]), 2); d['rsi5'] = rsi(closes, 5)
    d['last_5_closes_change_pct'] = round((closes[-1] / closes[-6] - 1) * 100, 2)
    m5 = chart('NQ%3DF', '2d', '5m'); y_close = closes[-1]
    over = [x for x in m5 if dt.datetime.fromtimestamp(x[0], NY) >= dt.datetime.combine(today - dt.timedelta(days=1), dt.time(18), NY)
            and dt.datetime.fromtimestamp(x[0], NY) < dt.datetime.combine(today, dt.time(9, 30), NY)]
    if over:
        d['overnight_change_pct'] = round((over[-1][4] / y_close - 1) * 100, 2)
        d['overnight_range_vs_avg20'] = round((max(x[2] for x in over) - min(x[3] for x in over)) / stt.mean(rng[-20:]), 2)
    vix = chart('%5EVIX', '1y', '1d'); vc = [c for *_, c in vix]
    d['vix'] = round(vc[-1], 2); d['vix_1y_percentile'] = round(100 * sum(1 for v in vc if v <= vc[-1]) / len(vc))
    third_fri = today.weekday() == 4 and 15 <= today.day <= 21
    d['calendar'] = [x for x, on in (('FOMC decision at 2pm today', today.isoformat() in FOMC), ('monthly options expiry (third Friday)', third_fri),
                                    ('first Friday: jobs report at 8:30am', today.weekday() == 4 and today.day <= 7)) if on] or ['nothing scheduled that Argon tracks']
    try:
        rss = get('https://feeds.finance.yahoo.com/rss/2.0/headline?s=%5EGSPC,%5ENDX&region=US&lang=en-US').decode('utf-8', 'ignore')
        d['headlines'] = [html.unescape(re.sub(r'<!\[CDATA\[|\]\]>', '', t)).strip() for t in re.findall(r'<item>.*?<title>(.*?)</title>', rss, re.S)][:12]
    except Exception: d['headlines'] = ['(headline feed unavailable)']
    return d

def dumb_rule(d):
    r = d['range_ratio']; return 1.5 if r > 1.2 else (0.5 if r < 0.8 else 1.0)

def ask(text):
    body = json.dumps({'model': MODEL, 'max_tokens': 300, 'temperature': 0, 'messages': [{'role': 'user', 'content': PROMPT + text}]}).encode()
    req = urllib.request.Request('https://api.anthropic.com/v1/messages', data=body, headers={'x-api-key': KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'})
    t = json.loads(urllib.request.urlopen(req, timeout=60).read())['content'][0]['text']
    j = json.loads(t[t.find('{'):t.rfind('}') + 1])
    size = min(SIZES, key=lambda s: abs(s - float(j.get('size', 1))))
    veto = j.get('veto') if j.get('veto') in VETOS else None
    return dict(trend_probability=max(0, min(100, float(j.get('trend_probability', 50)))), size=size, veto=veto, reason=str(j.get('reason', ''))[:300])

if __name__ == '__main__':
    now = dt.datetime.now(NY); today = now.date()
    force = '--force' in sys.argv
    if not force and (today.weekday() >= 5 or not (dt.time(8, 45) <= now.time() <= dt.time(9, 25))): print('daytype: outside 8:45-9:25 NY'); sys.exit(0)
    done = set()
    if os.path.exists(OUT):
        for ln in open(OUT):
            try: done.add(json.loads(ln)['date'])
            except Exception: pass
    if today.isoformat() in done and not force: print('daytype: already done today'); sys.exit(0)
    d = inputs(today); text = json.dumps(d, indent=1)
    runs = []
    if KEY:
        for _ in range(3):
            try: runs.append(ask(text))
            except Exception as e: print('run failed', repr(e)[:120])
    late = dt.datetime.now(NY).time() > dt.time(9, 25)
    if runs:
        sizes = sorted(r['size'] for r in runs); vetos = [r['veto'] for r in runs if r['veto']]
        ai = dict(size=sizes[len(sizes) // 2], trend_probability=round(stt.median(r['trend_probability'] for r in runs), 1),
                  veto=max(set(vetos), key=vetos.count) if len(vetos) >= 2 else None,      # a veto needs 2 of the 3 runs to agree
                  reason=runs[len(runs) // 2]['reason'])
    else: ai = dict(size=1.0, trend_probability=None, veto=None, reason='no forecast (no API key or all runs failed): counts as 1x')
    rec = dict(date=today.isoformat(), made_at=dt.datetime.now(NY).strftime('%H:%M'), late=late, inputs=d, ai=ai, ai_runs=runs, dumb_size=dumb_rule(d),
               ai_size_used=1.0 if (late or not runs) else (0.0 if ai['veto'] else ai['size']), model=MODEL, prompt_hash=PROMPT_HASH, shadow=True)
    if force and '--dry' in sys.argv: print(json.dumps(rec, indent=1)); sys.exit(0)
    open(OUT, 'a').write(json.dumps(rec) + '\n')
    print('daytype:', today, 'AI', ai['size'], ai['trend_probability'], ai['veto'], '| dumb', rec['dumb_size'], '| late' if late else '')
