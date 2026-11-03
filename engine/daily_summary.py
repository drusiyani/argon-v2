"""Plain-English AI daily summary for the desk (Task 2). Runs after the nightly book.

Facts only go in (the booked day from the ledger, the morning call, the checks); Claude writes 3-4 short sentences a
15-year-old could read. No key or a failed call -> a plain template from the same facts. Nothing here changes the book.
Writes docs/data/daily_summary.json (last 30 days). Usage: python engine/daily_summary.py"""
import os, sys, json, urllib.request, datetime as dt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'docs', 'data', 'daily_summary.json')
MODEL = 'claude-sonnet-5-5'
def J(*p, default=None):
    f = os.path.join(ROOT, *p)
    try: return json.load(open(f))
    except Exception: return default
def facts():
    lg = J('docs', 'data', 'ledger.json', default={}) or {}; days = lg.get('days') or []
    if not days: return None
    d = days[0]; st = lg.get('status') or {}
    calls = {}
    p = os.path.join(ROOT, 'data', 'daytype.jsonl')
    if os.path.exists(p):
        for ln in open(p):
            try: x = json.loads(ln); calls[x['date']] = x
            except Exception: pass
    c = calls.get(d['date']) or {}
    return dict(date=d['date'], book=lg.get('book'), status=d['status'], dollars=d['usd'], account=st.get('equity'),
                trades=[dict(strategy=t['strategy'], side=t['side'], contracts=t['contracts'], contract=t['contract'], entry_time=t['entry_time'],
                             exit_time=t['exit_time'], R=t['R'], usd=t['usd']) for t in d['trades']],
                skipped=[s['reason'] for s in d['skipped']], regime=(d.get('regime') or {}).get('label'),
                morning_call=dict(size=c.get('ai_size_used'), trend_probability=(c.get('ai') or {}).get('trend_probability'), shadow=True) if c else None,
                checks=st.get('checks'), band=(st.get('band') or {}).get('verdict'))
def template(f):
    n = len(f['trades']); w = sum(1 for t in f['trades'] if t['usd'] > 0)
    s = f"{f['date']}: {'no trades' if not n else f'{n} trade' + ('s' if n > 1 else '') + f', {w} winner' + ('s' if w != 1 else '')}, {f['dollars']:+,.0f} dollars."
    if f['regime']: s += f" The market was {f['regime']}."
    if f['skipped']: s += f" {len(f['skipped'])} trade(s) skipped by the rules."
    s += f" Account ${f['account']:,.0f}. Checks: {'all fine' if all(('ok' in str(v) or 'off' in str(v) or 'flat' in str(v)) for v in (f['checks'] or {}).values()) else 'something needs a look'}."
    return s
def claude(f):
    k = os.environ.get('ANTHROPIC_API_KEY')
    if not k: return None
    prompt = ('Write a plain-English summary of this paper-trading day for a 15-year-old, in 3 or 4 short sentences. '
              'Use only these facts. No advice, no hype, no predictions. Say it is paper trading. The morning call is shadow only (it does not change the trades).\n\n' + json.dumps(f))
    body = json.dumps({'model': MODEL, 'max_tokens': 220, 'temperature': 0, 'messages': [{'role': 'user', 'content': prompt}]}).encode()
    req = urllib.request.Request('https://api.anthropic.com/v1/messages', data=body, headers={'x-api-key': k, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())['content'][0]['text'].strip()
if __name__ == '__main__':
    f = facts()
    if not f: print('nothing booked yet'); sys.exit(0)
    old = J('docs', 'data', 'daily_summary.json', default={}) or {}
    if f['date'] in old: print('already summarised', f['date']); sys.exit(0)
    try: text, by = claude(f), 'Claude'
    except Exception as e: print('AI summary failed:', e); text = None
    if not text: text, by = template(f), 'template (no AI)'
    old[f['date']] = dict(text=text, by=by, made=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC'))
    json.dump(dict(sorted(old.items())[-30:]), open(OUT, 'w'), indent=1); print(f['date'], by, text)
