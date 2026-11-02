"""One-command replay of any day (Task 1 extra e): runs the exact book code and shows that day's trades, minute by minute
times, prices, R and dollars, and compares it with the ledger if the day was booked.
Usage: python engine/replay.py 2026-10-16 [official|practice]"""
import os, sys, json, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'engine'))
import live
d = sys.argv[1]; name = sys.argv[2] if len(sys.argv) > 2 else 'practice'
sk = []; tr = [t for t in live.P.book(1.0, skipped=sk) if t['date'] == d]; sk = [t for t in sk if t['date'] == d]
S = live.sessions(); print(f"{d}: {live.status_of(S.get(d, 0))} ({S.get(d, 0)} regular-session minutes), roll day: {d in live.c.roll('NQ')}, FOMC: {d in live.c.FOMC}")
for t in tr:
    print(f"  {live.tid(t):40s} {'long ' if t['side'] == 1 else 'short'} {live.hm(t['entry_min'])}-{live.hm(t['exit_min'])}  entry {t['entry']:.2f} stop {t['stop']:.2f} exit {t['exit']:.2f}  {t['gross'] - t['cost']:+.3f}R")
for t in sk: print(f"  skipped by the cost rule: {live.tid(t)} (cost {t['cost']:.3f}R)")
if not tr and not sk: print('  no trades')
L = {e['date']: e for e in live.read(os.path.join(ROOT, live.BOOKS[name]['folder'], 'ledger.jsonl'))}
if d in L:
    e = L[d]; ok = sorted(x['id'] for x in e['trades']) + sorted(x['id'] for x in e['skipped'] if x['reason'].startswith('size'))
    same = sorted(live.tid(t) for t in tr) == sorted(ok)
    print(f"ledger ({name}): {len(e['trades'])} trades, ${e['equity_end'] - e['equity_start']:+,.2f}, hash {e['hash'][:12]}, code {e['code_commit']}  ->  {'MATCHES' if same else 'DIFFERENT'}")
