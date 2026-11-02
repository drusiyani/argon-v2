"""Health alarms to Dru's phone through ntfy.sh (Task 1 extra b).

The topic name lives in the GitHub secret NTFY_TOPIC (anyone who knows a ntfy topic can read it, so keep it long and random).
Without the secret, alerts are only printed. Every alert is also kept in data/alerts.jsonl so the desk can show it.
Usage: python engine/alert.py "title" "message" [high]"""
import os, sys, json, urllib.request, datetime as dt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, 'data', 'alerts.jsonl')

def send(title, msg, priority='default', tags='warning'):
    rec = dict(at=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), title=title, msg=msg, priority=priority)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, 'a') as f: f.write(json.dumps(rec) + '\n')
    topic = os.environ.get('NTFY_TOPIC')
    print(f'ALERT [{priority}] {title}: {msg}')
    if not topic: return False
    try:
        req = urllib.request.Request(f'https://ntfy.sh/{topic}', data=msg.encode(), method='POST',
                                     headers={'Title': title.encode('ascii', 'ignore').decode(), 'Priority': priority, 'Tags': tags})
        urllib.request.urlopen(req, timeout=20).read(); return True
    except Exception as e: print('ntfy failed:', e); return False

if __name__ == '__main__':
    a = sys.argv[1:] + ['', '']
    send(a[0] or 'Argon', a[1] or '(no message)', a[2] or 'default')
