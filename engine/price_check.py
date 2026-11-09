"""Second price source (Amendment 9): each night, compare Databento's NQ daily close with Yahoo's NQ=F for the last 10 sessions.
A gap over 1% (outside roll days, when the two can be on different contracts) is flagged and alerts the phone, so bad data
is caught before it's trusted. Writes data/price_check.json. Usage: python engine/price_check.py"""
import os, sys, json, datetime as dt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'engine'))
import portfolio as P, daytype
from zoneinfo import ZoneInfo
NY = ZoneInfo('America/New_York'); c = P.c
D, dl, _ = c.daily('NQ'); rolls = set(c.roll('NQ'))
y = {dt.datetime.fromtimestamp(t, NY).date().isoformat(): cl for t, o, h, l, cl in daytype.chart('NQ%3DF', '1mo', '1d')}
rows, flags = [], []
for d in dl[-10:]:
    if d not in y: continue
    gap = (D[d]['c'] / y[d] - 1) * 100; rows.append(dict(date=d, databento=D[d]['c'], yahoo=round(y[d], 2), gap_pct=round(gap, 3), roll=d in rolls))
    if abs(gap) > 1 and d not in rolls: flags.append(d)
json.dump(dict(checked=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), rows=rows, flagged=flags), open(os.path.join(ROOT, 'data', 'price_check.json'), 'w'), indent=1)
print('price check:', len(rows), 'days,', 'flagged ' + ', '.join(flags) if flags else 'all within 1%')
if flags:
    import alert; alert.send('Argon: price mismatch', f"Databento and Yahoo disagree by over 1% on {', '.join(flags)}. Check the data before trusting those days.", 'high')
