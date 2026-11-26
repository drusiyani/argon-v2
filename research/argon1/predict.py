"""Argon-1's live 08:45 call (shadow seat). Runs in the desk job on the runner; no API cost.

Reads the frozen model from $ARGON1_MODEL_DIR (private data repo), builds today's inputs from Yahoo's delayed
5-minute NQ=F / ES=F bars and the VIX's daily closes, and appends one line to data/argon1.jsonl.
Acts once a day, between 08:45 and 09:25 New York, like the AI seats. Known gap: Yahoo's continuous contract has no
contract id, so a roll-night jump is not zeroed as it is in training (about 4 mornings a year; logged as `roll_risk`).
"""
import os, sys, json, hashlib, datetime as dt
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
from argon1 import data as D, models as M
from zoneinfo import ZoneInfo
NY = ZoneInfo('America/New_York'); ROOT = D.ROOT
LOG = os.path.join(ROOT, 'data', 'argon1.jsonl')


def yahoo(sym, rng, iv):
    sys.path.insert(0, os.path.join(ROOT, 'engine'))
    import daytype
    r = json.loads(daytype.get(f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range={rng}&interval={iv}'))['chart']['result'][0]
    q = r['indicators']['quote'][0]
    return [(t, o, h, l, c, v or 0) for t, o, h, l, c, v in zip(r['timestamp'], q['open'], q['high'], q['low'], q['close'], q['volume'])
            if None not in (o, h, l, c)]


def bars_from(rows):
    m = pd.DataFrame(rows, columns=['t', 'open', 'high', 'low', 'close', 'volume'])
    m['ts'] = pd.to_datetime(m['t'], unit='s', utc=True); m['instrument_id'] = 0
    return D.five_minute(m[['ts', 'open', 'high', 'low', 'close', 'volume', 'instrument_id']])


def size_of(p, cut):
    return 2.0 if p >= cut['two'] else 1.5 if p >= cut['one_and_half'] else 0.5 if p < cut['half'] else 1.0


def run(force=False):
    now = dt.datetime.now(NY); today = now.date().isoformat()
    if not force and not (now.weekday() < 5 and dt.time(8, 45) <= now.time() <= dt.time(9, 25)): return print('argon1: outside 08:45-09:25')
    sys.path.insert(0, os.path.join(ROOT, 'engine')); from calendar_us import HOLIDAYS
    if not force and today in HOLIDAYS: return print('argon1: US market holiday')
    if os.path.exists(LOG) and any(json.loads(l).get('date') == today for l in open(LOG)): return print('argon1: already called today')
    md = os.environ.get('ARGON1_MODEL_DIR', os.path.join(ROOT, 'data', 'argon1', 'argon1'))
    meta = json.load(open(os.path.join(md, 'meta.json')))
    for f, h in meta['files'].items():
        if hashlib.sha256(open(os.path.join(md, f), 'rb').read()).hexdigest() != h: sys.exit(f'argon1: {f} does not match its frozen fingerprint')
    bars = {s: bars_from(yahoo(f'{s}%3DF', '60d', '5m')) for s in D.SYMS}
    vix = {dt.datetime.fromtimestamp(t, NY).date().isoformat(): c for t, o, h, l, c, v in yahoo('%5EVIX', '2y', '1d')}
    F = D.build(bars, vix, fomc=None, first=today, last=today, today=today)
    if not len(F['dates']) or F['dates'][-1] != today: sys.exit('argon1: not enough bars before 08:45 to build today\'s inputs')
    std = None
    if meta['chosen'] == 'A':
        z = np.load(os.path.join(md, 'model_a.npz'))
        pcas = [M.PCA.load(dict(mu=z[f'pca{s}_mu'], W=z[f'pca{s}_W'])) for s in range(len(D.SYMS))]
        std = M.Std.load(dict(m=z['ctx_m'], s=z['ctx_s'])); xs = M.Std.load(dict(m=z['xs_m'], s=z['xs_s']))
        tok, mdl = M.kronos_load(os.environ.get('KRONOS_DIR', os.path.join(ROOT, 'vendor', 'Kronos')))
        emb = M.kronos_embed(F['raw'], F['stamp'], tok, mdl)
        X = xs(M.a_features(emb, std(F['ctx']), pcas)); p = float(1 / (1 + np.exp(-(X @ z['coef'].T + z['intercept'])))[0, 0])
    else:
        import torch
        z = np.load(os.path.join(md, 'ctx_std.npz')); std = M.Std.load(dict(m=z['m'], s=z['s']))
        net = M.tiny_net(len(D.CTX_FEATS)); net.load_state_dict(torch.load(os.path.join(md, 'model_b.pt'), weights_only=True))
        p = float(M.predict_tiny(net, F['seq'], std(F['ctx']))[0])
    jump = max(abs(F['seq'][0, s, :, 0]).max() for s in range(len(D.SYMS)))
    row = dict(date=today, made_at=now.strftime('%H:%M'), seat='argon1', version=meta['version'], model=meta['chosen'],
               p_trend=round(p, 4), size=size_of(p, meta['cutoffs']), inputs={k: round(float(v), 4) for k, v in zip(D.CTX_FEATS, F['ctx'][0])},
               roll_risk=bool(jump >= 1.0), source='Yahoo 5-minute NQ=F / ES=F (delayed), VIX daily close')
    with open(LOG, 'a') as f: f.write(json.dumps(row) + '\n')
    print('argon1:', row['p_trend'], row['size'])


if __name__ == '__main__':
    run(force='--force' in sys.argv)
