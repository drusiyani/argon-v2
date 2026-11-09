"""'What am I holding?' (Task 1). Prints the paper account and every open position, from the official ledger and the
unofficial live view. Usage: python engine/holding.py [official|practice]"""
import os, sys, json, datetime as dt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS = dict(official='data/ledger', practice='data/ledger_practice')
name = sys.argv[1] if len(sys.argv) > 1 else ('practice' if dt.date.today() < dt.date(2027, 2, 1) else 'official')
st = os.path.join(ROOT, BOOKS[name], 'status.json')
if not os.path.exists(st): print(f'{name} book: nothing booked yet'); sys.exit(0)
s = json.load(open(st))
print(f"{name} book ({s.get('state')}), last booked {s.get('last_booked')}, last run {s.get('run_at')}")
print(f"  account ${s.get('equity', 100000):,.2f}   double-cost account ${s.get('equity_2x', 100000):,.2f}")
print(f"  checks: " + '; '.join(f'{k} {v}' for k, v in s.get('checks', {}).items()))
print('  official open positions: none (every strategy is flat by 15:55 New York)' if 'flat' in s.get('checks', {}).get('positions', '') else '  POSITION CHECK FAILED: ' + s['checks'].get('positions', '?'))
lv = os.path.join(ROOT, 'docs', 'data', 'live_view.json')
if os.path.exists(lv):
    v = json.load(open(lv)); opn = [t for t in v.get('trades', []) if t.get('state') == 'open']
    print(f"  live view (UNOFFICIAL, Yahoo, as of {v.get('as_of')}): " + ('nothing open' if not opn else ''))
    for t in opn: print(f"    {t['side']} {t['contracts']} {t['contract']} ({t['strategy']}) from {t['entry']} at {t['entry_time']}, stop {t['stop']}, now {t['last']} = {t['R_now']:+.2f}R")
