"""Batch 29 step 1 (run once per era). Rules and marks: analysis/BATCH29_PREREG.md (committed before this file ran).
Dumps to analysis/_cache/batch29_{era}.pkl: every variant's trades net and friction-free, the noise band on shifted
clocks, 1-minute session closes, and pre-market minutes 08:25-09:30."""
import os, sys, csv, gzip, glob, pickle, inspect, collections, datetime as dt
from zoneinfo import ZoneInfo
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'engine'))
import portfolio as P
c = P.c; ERA = os.environ.get('ARGON_DATA', 'databento'); NYZ = ZoneInfo('America/New_York'); kw = P.CONFIG['strategies']
LO, HI = (('2021-01-01', '2026-12-31') if ERA == 'databento' else ('2010-07-01', '2020-12-31'))
keep = lambda L: [t for t in L if LO <= t['date'] <= HI]
# shifted-clock noise band: same code, decision bars moved by OFF minutes (start and cutoff move with it)
src = inspect.getsource(c.noiseband).replace('def noiseband(', 'def noiseband_off(').replace('(m - 570) % freq != freq - 1', '(m - 570 + OFF) % freq != freq - 1')
assert 'OFF' in src
exec(src, c.__dict__)
def nb_off(off):
    c.OFF = off; return c.noiseband_off('NQ', start=600 - off, cutoff=930 - off, **kw['noiseband'])
def run():
    out = dict(quantlab=c.quantlab('NQ', **kw['quantlab']), noiseband=c.noiseband('NQ', **kw['noiseband']), atrband=c.atrband('NQ', **kw['atrband']))
    c.OFF = 0; chk = c.noiseband_off('NQ', start=600, cutoff=930, **kw['noiseband'])
    assert len(chk) == len(out['noiseband']) and all(a == b for a, b in zip(chk, out['noiseband'])), 'patched noise band differs from the original at OFF=0'
    out['nb_E5'] = nb_off(5); out['nb_L5'] = nb_off(-5)
    return {k: keep(v) for k, v in out.items()}
NET = run()
SL0, C0 = dict(c.SL), dict(c.COST); c.SL = {k: 0.0 for k in SL0}; c.COST = {k: 0.0 for k in C0}
FREE = run(); c.SL, c.COST = SL0, C0
# 1-minute session bars (open, close, volume) for the candle shape, day/night and entry-to-close moves
NB, _ = c.nb_load('NQ'); M1 = {d: [(b[0], b[1], b[2], b[3], b[4], b[5]) for b in v] for d, v in NB.items() if LO <= d <= HI or d >= '2010-06-01'}
# pre-market minutes 08:25-09:30 from the raw files
dirn = os.path.join(ROOT, 'data', 'databento' if ERA == 'databento' else ERA); PM = collections.defaultdict(dict); off = {}
for f in sorted(glob.glob(os.path.join(dirn, 'NQ_*.csv.gz'))):
    with gzip.open(f, 'rt') as fh:
        for r in csv.DictReader(fh):
            ts = r['ts_event']; dk = ts[:13]
            if dk not in off:
                u = dt.datetime(int(ts[:4]), int(ts[5:7]), int(ts[8:10]), int(ts[11:13]), tzinfo=dt.timezone.utc).astimezone(NYZ); off[dk] = (u.date().isoformat(), u.hour)
            d, hr = off[dk]; m = hr * 60 + int(ts[14:16])
            if 505 <= m < 570: PM[d][m] = (m, float(r['open']), float(r['high']), float(r['low']), float(r['close']), float(r['volume'] or 0))
PM = {d: sorted(v.values()) for d, v in PM.items()}
pickle.dump(dict(era=ERA, net=NET, free=FREE, m1=M1, pm=PM, sl=SL0['NQ'], cost=C0['NQ']), open(os.path.join(ROOT, 'analysis', '_cache', f'batch29_{ERA}.pkl'), 'wb'))
print('ok', ERA, {k: len(v) for k, v in NET.items()}, {k: len(v) for k, v in FREE.items()}, len(M1), len(PM))
