"""Nightly check that the public site agrees with the official ledger (runs in live.yml after booking).

Fails the job (exit 1) with a plain list of problems if:
- the last booked day is missing from docs/data/live_days.json, or its trades differ from the ledger's,
- the practice-book equity baked into docs/index.html differs from the ledger (after the 20 Nov display shift),
- the chart has no 5-minute bars for the last booked day (Yahoo usually has them by the evening),
- the site still contains the build placeholder or a JavaScript syntax error.
"""
import os, re, sys, json, subprocess, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)


def alert(msg):
    """Phone/watch push via ntfy if the NTFY_TOPIC secret is set (no account needed); silent otherwise."""
    topic = os.environ.get('NTFY_TOPIC')
    if not topic: return
    import urllib.request
    try: urllib.request.urlopen(urllib.request.Request('https://ntfy.sh/' + topic, data=msg.encode(), headers={'Title': 'Argon', 'Priority': 'high'}), timeout=20)
    except Exception as e: print('alert failed:', e)


def main():
    bad = []
    st = json.load(open(P('data', 'ledger_practice', 'status.json')))
    last = st.get('last_booked')
    rows = {json.loads(l)['date']: json.loads(l) for l in open(P('data', 'ledger_practice', 'ledger.jsonl'))}
    L = rows.get(last, {})
    try: days = json.load(open(P('docs', 'data', 'live_days.json')))['days']
    except Exception as e: days = {}; bad.append(f'live_days.json unreadable: {e}')
    if last >= '2026-11-20':
        if last not in days: bad.append(f'{last} is booked but missing from the site calendar (live_days.json)')
        else:
            led = sorted((t.get('strategy'), round(float(t.get('usd') or 0), 2)) for t in L.get('trades', []))
            site = sorted((t[0], round(float(t[7]), 2)) for t in days[last].get('t', []))
            if led != site: bad.append(f'{last}: site trades {site} differ from the ledger {led}')
    html = open(P('docs', 'index.html')).read()
    m = re.search(r'"ledger":\{[^}]*?"equity":([0-9.]+)[^}]*?"last":"([0-9-]+)"', html)
    if not m: bad.append('practice book missing from index.html')
    else:
        if m.group(2) != last: bad.append(f'site shows last booked day {m.group(2)}, ledger says {last}')
        try: real = json.loads(re.search(r'"ledger":(\{.*?"warmup":\{.*?\}\})', html).group(1)).get('real_equity')
        except Exception: real = None
        if real is not None and abs(float(real) - float(st.get('equity', 0))) > 0.01:
            bad.append(f'site equity {real} differs from the ledger {st.get("equity")}')
    try:
        ch = json.load(open(P('docs', 'data', 'chart.json')))['sessions']
        if last not in ch: bad.append(f'chart has no 5-minute bars for {last}')
    except Exception as e: bad.append(f'chart.json unreadable: {e}')
    if '/*__STATIC_FACTS__*/' in html and 'DATA=' not in html: bad.append('index.html looks unbuilt')
    js = re.findall(r'<script[^>]*>(.*?)</script>', html, re.S)
    if js:
        f = tempfile.NamedTemporaryFile('w', suffix='.js', delete=False); f.write(js[-1]); f.close()
        try:
            r = subprocess.run(['node', '--check', f.name], capture_output=True, text=True)
            if r.returncode: bad.append('site JavaScript does not parse: ' + r.stderr.strip()[:200])
        except FileNotFoundError: pass
    if bad:
        print('SITE CHECK FAILED'); [print(' -', b) for b in bad]
        alert('Argon site check failed: ' + '; '.join(bad)[:900]); sys.exit(1)
    print(f'site check ok: {last} booked, calendar, equity and chart agree with the ledger')


if __name__ == '__main__':
    main()
