"""Public timestamp for the ledger (Amendment 9). Every night the ledger's latest hash is written to a small file and stamped
with OpenTimestamps, which anchors it into the Bitcoin blockchain through free public servers. After that, nobody (Dru
included) can rewrite the ledger's history without it showing, even by force-pushing the GitHub repo.
Check a stamp: `ots verify data/stamps/<file>.ots`. Usage: python engine/stamp.py"""
import os, json, glob, datetime as dt, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(ROOT, 'data', 'stamps'); os.makedirs(OUT, exist_ok=True)
for name, folder in (('official', 'data/ledger'), ('practice', 'data/ledger_practice')):
    p = os.path.join(ROOT, folder, 'ledger.jsonl')
    if not os.path.exists(p): continue
    last = [x for x in open(p) if x.strip()]
    if not last: continue
    e = json.loads(last[-1]); f = os.path.join(OUT, f"{name}-{e['date']}.txt")
    if os.path.exists(f + '.ots'): continue
    open(f, 'w').write(f"Argon v2 {name} ledger\nlast booked day: {e['date']}\nhead hash: {e['hash']}\nstamped: {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}\n")
    r = subprocess.run(['ots', 'stamp', f], capture_output=True, text=True); print(name, e['date'], 'stamped' if r.returncode == 0 else 'stamp failed: ' + r.stderr[-200:])
for f in glob.glob(os.path.join(OUT, '*.ots')): subprocess.run(['ots', 'upgrade', f], capture_output=True)   # completes once Bitcoin confirms
