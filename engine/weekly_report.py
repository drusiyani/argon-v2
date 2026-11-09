"""Weekly auto-report into the Obsidian vault (Task 1 extra f). Writes vault/Live/<year>-W<week>.md from the ledger.
Usage: python engine/weekly_report.py [official|practice]   (the workflow runs it on Fridays)"""
import os, sys, json, collections, datetime as dt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'engine'))
BOOKS = dict(official='data/ledger', practice='data/ledger_practice')
def read(p): return [json.loads(x) for x in open(p) if x.strip()] if os.path.exists(p) else []
def report(name, today=None):
    today = today or dt.date.today(); y, w, _ = today.isocalendar(); mon = today - dt.timedelta(days=today.weekday())
    L = read(os.path.join(ROOT, BOOKS[name], 'ledger.jsonl')); wk = [e for e in L if mon.isoformat() <= e['date'] <= today.isoformat()]
    if not wk: return None
    st = json.load(open(os.path.join(ROOT, BOOKS[name], 'status.json'))); rp = os.path.join(ROOT, BOOKS[name], 'regime.json')
    reg = json.load(open(rp)) if os.path.exists(rp) else {}
    by = collections.defaultdict(lambda: [0, 0.0, 0.0])
    for e in wk:
        for t in e['trades']: x = by[t['strategy']]; x[0] += 1; x[1] += t['R']; x[2] += t['usd']
    usd = wk[-1]['equity_end'] - wk[0]['equity_start']
    lines = [f"# Argon {name} book: week {y}-W{w:02d}", '', f"#argon/live  ·  [[Home]]", '',
             f"- Account: ${wk[0]['equity_start']:,.0f} → **${wk[-1]['equity_end']:,.0f}** ({usd:+,.0f}, {usd / wk[0]['equity_start'] * 100:+.2f}%)",
             f"- Since the start: ${st.get('equity', 0):,.0f} (double costs: ${st.get('equity_2x', 0):,.0f})",
             f"- Checks: " + '; '.join(f'{k} {v}' for k, v in st.get('checks', {}).items()),
             f"- Backtest band: {(st.get('band') or {}).get('verdict', 'n/a')}", '', '## By strategy', '', '| strategy | trades | R | $ |', '|---|---|---|---|']
    lines += [f'| {k} | {v[0]} | {v[1]:+.2f} | {v[2]:+,.0f} |' for k, v in sorted(by.items())]
    lines += ['', '## Days', '', '| date | regime | trades | $ | hash |', '|---|---|---|---|---|']
    lines += [f"| {e['date']} | {(reg.get(e['date']) or {}).get('label', '')} | {len(e['trades'])} | {e['equity_end'] - e['equity_start']:+,.0f} | `{e['hash'][:12]}` |" for e in wk]
    sk = [s for e in wk for s in e['skipped']]
    if sk: lines += ['', '## Skipped', ''] + [f"- {s['id']}: {s['reason']}" for s in sk]
    lines += ['', '_Written automatically from the hash-chained ledger. The ledger is the record; this page is a summary._']
    p = os.path.join(ROOT, 'vault', 'Live', f'{y}-W{w:02d}.md'); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'w').write('\n'.join(lines) + '\n'); return p
if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else ('practice' if dt.date.today() < dt.date(2027, 2, 1) else 'official')
    print(report(name) or 'no booked days this week')
