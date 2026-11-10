"""Analysis only (does not touch the race): what did the book's S&P (ES) trades make, vs its Nasdaq (NQ) trades?
Uses the official book code unchanged. Writes analysis/es_leg.json."""
import os, sys, json, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'engine'))
import portfolio as P
c = P.c
tr = P.book(1.0); risk = P.CONFIG['risk_pct']
net = lambda t: t['w'] * (t['gross'] - t['cost'])
out = {'note': 'Backtest, 1% risk per trade, after costs, mostly in-sample. ES trades come only from the expiry rule (third Friday).', 'years': {}}
for y in sorted({t['date'][:4] for t in tr}):
    row = {}
    for sym in ('ES', 'NQ'):
        ts = [t for t in tr if t['sym'] == sym and t['date'][:4] == y]
        months = c.months_between(f'{y}-01' if y != '2021' else min(t['month'] for t in tr), max(t['month'] for t in tr) if y == max(t['date'][:4] for t in tr) else f'{y}-12')
        cv = P.curve(ts, months, 1.0, risk) if ts else None
        row[sym] = dict(trades=len(ts), wins=sum(net(t) > 0 for t in ts), R=round(sum(net(t) for t in ts), 2),
                        pct=round((cv['final'] / P.CONFIG['start_usd'] - 1) * 100, 1) if cv else 0.0)
    out['years'][y] = row
y26 = [t for t in tr if t['sym'] == 'ES' and t['date'][:4] == '2026']
out['es_2026_trades'] = [dict(date=t['date'], side='long' if t['side'] == 1 else 'short', R=round(net(t), 2)) for t in y26]
os.makedirs(os.path.join(ROOT, 'analysis'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'analysis', 'es_leg.json'), 'w'), indent=1)
print(json.dumps(out['years'], indent=1)); print(out['es_2026_trades'])
