"""Batch 35: minimum stop distance for Opening Drive (rules: analysis/BATCH35_PREREG.md)."""
import os, sys, json, math, datetime as dt, statistics as stt
A = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(A)
sys.path.insert(0, os.path.join(ROOT, 'research')); sys.path.insert(0, os.path.join(ROOT, 'engine'))
import common as c
from portfolio import CONFIG
ERA = c.DATA; RISK = 0.5; CAP = CONFIG['cost_cap_R']; KW = CONFIG['strategies']

def others():
    return (c.walkforward(c.noiseband('NQ', **KW['noiseband']), 1.0) + c.atrband('NQ', **KW['atrband'])
            + c.opex('NQ', **KW['expiry']) + c.opex('ES', **KW['expiry']))

def stats(trades, days):
    day = {d: 0.0 for d in days}
    for t in trades: day[t['date']] = day.get(t['date'], 0.0) + RISK * (t['gross'] - t['cost'])
    r = [day[d] for d in sorted(day)]; m = stt.mean(r); sd = stt.pstdev(r)
    cum = pk = dd = 0.0
    for x in r: cum += x; pk = max(pk, cum); dd = max(dd, pk - cum)
    return dict(sharpe=round(m / sd * math.sqrt(252), 3) if sd else 0, total_R=round(sum(r) / RISK, 1), worst_drop_pct=round(dd, 2))

def main():
    rest = [t for t in others() if t['cost'] <= CAP]
    allt = rest + c.walkforward(c.quantlab('NQ', **KW['quantlab']), 1.0)
    d0, d1 = min(t['date'] for t in allt), max(t['date'] for t in allt)
    days = [d.isoformat() for d in (dt.date.fromisoformat(d0) + dt.timedelta(k) for k in range((dt.date.fromisoformat(d1) - dt.date.fromisoformat(d0)).days + 1)) if d.weekday() < 5]
    out = dict(era=ERA, period=[d0, d1], variants={})
    for name, extra in [('current', {})] + [(f'{m} k={k}', dict(min_stop_atr=k, min_stop_mode=m)) for m in ('widen', 'skip') for k in (0.02, 0.04, 0.06)]:
        ql = [t for t in c.walkforward(c.quantlab('NQ', **KW['quantlab'], **extra), 1.0) if t['cost'] <= CAP]
        s = stats(rest + ql, days)
        s['opening_drive'] = dict(trades=len(ql), avg_R=round(stt.mean([t['gross'] - t['cost'] for t in ql]), 3) if ql else None,
                                  total_R=round(sum(t['gross'] - t['cost'] for t in ql), 1))
        out['variants'][name] = s; print(name, s, flush=True)
    json.dump(out, open(f'{A}/batch35_{ERA}.json', 'w'), indent=1)

main()
