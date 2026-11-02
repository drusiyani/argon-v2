"""Nightly top-up of Databento 1-minute data for the live ledger (Task 1).

Downloads only the minutes we don't have yet (from each market's last saved bar to Databento's latest available minute)
into small files data/databento/{SYM}_d{YYYY-MM-DD}.csv.gz. Same dataset, schema and continuous front-month symbols
as the backtest, so the live book reads exactly what the research read. All FOUR markets are fetched, because the engine
only keeps days that every market has, and roll days are found from those days (council point 3).

Costs pennies (about $0.005 per market per day). Hard cap LIVE_MAX_USD (default $2) per run.
When the monthly job saves a full month file, the daily files it covers are deleted (the loaders keep one bar per minute anyway).
Usage: python engine/fetch_live.py      (needs DATABENTO_API_KEY; without it, it does nothing)"""
import os, sys, gzip, glob, json, datetime as dt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'engine'))
OUT = os.path.join(ROOT, 'data', 'databento')
MAX_USD = float(os.environ.get('LIVE_MAX_USD', '2'))

def files(sym): return sorted(glob.glob(os.path.join(OUT, f'{sym}_*.csv.gz')))

def last_bar(sym):
    """Latest ts_event saved for this market (reads only files from the last two years, newest first)."""
    best = None; y = dt.date.today().year
    for f in files(sym):
        tag = os.path.basename(f)[len(sym) + 1:-7]
        if not (tag.startswith('d') or tag[:4].isdigit() and int(tag[:4]) >= y - 1): continue
        with gzip.open(f, 'rt') as fh:
            last = None
            for line in fh: last = line
        if last and last[:4].isdigit():
            ts = last.split(',')[0][:19]
            if best is None or ts > best: best = ts
    return best

def tidy():
    """Delete daily files fully covered by monthly files (the month of the file's date and of 3 days before it)."""
    gone = 0
    for f in glob.glob(os.path.join(OUT, '*_d????-??-??.csv.gz')):
        b = os.path.basename(f); sym = b.split('_')[0]; d = dt.date.fromisoformat(b[len(sym) + 2:len(sym) + 12])
        need = {f'{(d - dt.timedelta(days=3)):%Y-%m}', f'{d:%Y-%m}'}
        if all(os.path.exists(os.path.join(OUT, f'{sym}_{m}.csv.gz')) for m in need): os.remove(f); gone += 1
    return gone

def available_end(fd):
    try:
        r = fd.call('metadata.get_dataset_range', dict(dataset='GLBX.MDP3'))
        e = r.get('end') or r.get('end_date')
        if e: return dt.datetime.fromisoformat(e[:19]) if 'T' in e else dt.datetime.fromisoformat(e[:10])   # UTC
    except Exception as ex: print('dataset range unavailable:', ex)
    return dt.datetime.utcnow() - dt.timedelta(minutes=30)

def run():
    import fetch_databento as fd
    if not fd.KEY: print('No DATABENTO_API_KEY set, skipping the top-up.'); return dict(status='no key')
    end = available_end(fd).replace(second=0, microsecond=0); jobs = []
    for m, sym in fd.MARKETS.items():
        lb = last_bar(m)
        if lb is None: print(m, 'has no data yet: run the backfill first'); continue
        start = dt.datetime.fromisoformat(lb) + dt.timedelta(minutes=1)
        if start >= end: continue
        jobs.append((m, sym, start.isoformat(), end.isoformat()))
    if not jobs: print('all markets up to date'); return dict(status='up to date', end=end.isoformat(), tidied=tidy())
    cost = sum(float(fd.call('metadata.get_cost', fd.params(sym, a, b))) for m, sym, a, b in jobs)
    print(f'{len(jobs)} top-ups, estimated ${cost:.4f}')
    if cost > MAX_USD: raise SystemExit(f'top-up would cost ${cost:.2f}, over the ${MAX_USD} cap: stopping')
    saved = {}
    for m, sym, a, b in jobs:
        data = fd.call('timeseries.get_range', dict(fd.params(sym, a, b), encoding='csv', pretty_px='true', pretty_ts='true',
                                                     map_symbols='true', compression='none'), raw=True)
        if data.count(b'\n') <= 1: print(m, 'no new bars'); continue
        path = os.path.join(OUT, f'{m}_d{b[:10]}.csv.gz')
        if os.path.exists(path):          # a second run on the same day: keep both, the loaders drop duplicate minutes
            path = os.path.join(OUT, f'{m}_d{b[:10]}-{b[11:13]}{b[14:16]}.csv.gz')
        with gzip.open(path, 'wb') as f: f.write(data)
        saved[m] = os.path.basename(path); print('saved', saved[m], data.count(b'\n') - 1, 'bars')
    return dict(status='ok', end=end.isoformat(), usd=round(cost, 4), saved=saved, tidied=tidy())

if __name__ == '__main__':
    print(json.dumps(run()))
