"""Top up the two public daily series the package's core needs (Amendment 13), from FRED:
  VXNCLS (CBOE Nasdaq-100 volatility index)  -> analysis/vxn.csv          (date,vxn)
  DTB3   (3-month T-bill rate, %)            -> analysis/tbill_dtb3.csv   (date,dtb3_pct)
Only dates after the file's last row are added; existing rows are never changed (booked days read saved inputs anyway).
A failed download leaves the file as it is; engine/core.py then uses the last value it has, or w = 1 if it is stale."""
import os, csv, io, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERIES = (('VXNCLS', 'vxn.csv', 'vxn'), ('DTB3', 'tbill_dtb3.csv', 'dtb3_pct'))

def top_up(sid, fn, col):
    path = os.path.join(ROOT, 'analysis', fn)
    rows = list(csv.DictReader(open(path))) if os.path.exists(path) else []
    last = rows[-1]['date'] if rows else '0000-00-00'
    req = urllib.request.Request(f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd={last[:4] or "2009"}-01-01',
                                 headers={'User-Agent': 'argon-v2 (paper-trading research)'})
    text = urllib.request.urlopen(req, timeout=30).read().decode()
    new = []
    for r in csv.reader(io.StringIO(text)):
        if len(r) < 2 or not r[0][:4].isdigit(): continue
        d, v = r[0], r[1].strip()
        if d > last and v not in ('', '.'):
            try: new.append((d, float(v)))
            except ValueError: pass
    if new:
        with open(path, 'a', newline='') as f:
            w = csv.writer(f)
            if not rows: w.writerow(['date', col])
            for d, v in new: w.writerow([d, v])
    print(f'{sid}: {len(new)} new rows, last {new[-1][0] if new else last}')

if __name__ == '__main__':
    for s in SERIES:
        try: top_up(*s)
        except Exception as e: print(f'{s[0]} skipped: {e}')
