"""Batch 38: trend filter on the Nasdaq core (rules: analysis/BATCH38_PREREG.md)."""
import os, sys, json, math, csv, bisect, statistics as stt
A = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(A)
sys.path.insert(0, os.path.join(ROOT, 'research')); sys.path.insert(0, os.path.join(ROOT, 'engine'))
import common as c
from portfolio import CONFIG
ERA = c.DATA; RISK = 0.5; CAP = CONFIG['cost_cap_R']; KW = CONFIG['strategies']

def rules_daily():
    tr = (c.walkforward(c.quantlab('NQ', **KW['quantlab']), 1.0) + c.walkforward(c.noiseband('NQ', **KW['noiseband']), 1.0)
          + c.atrband('NQ', **KW['atrband']) + c.opex('NQ', **KW['expiry']) + c.opex('ES', **KW['expiry']))
    out = {}
    for t in tr:
        if t['cost'] <= CAP: out[t['date']] = out.get(t['date'], 0.0) + RISK * (t['gross'] - t['cost']) / 100
    return out

def stats(r):
    eq = 1.0; pk = 1.0; dd = 0.0
    for x in r: eq *= 1 + x; pk = max(pk, eq); dd = max(dd, 1 - eq / pk)
    yrs = len(r) / 252
    return dict(cagr=round((eq ** (1 / yrs) - 1) * 100, 1), sharpe=round(stt.mean(r) / stt.pstdev(r) * math.sqrt(252), 3), worst_drop=round(dd * 100, 1))

def main():
    D, dl, _ = c.daily('NQ'); R = c.roll('NQ')
    V = {}
    for row in csv.DictReader(open(os.path.join(ROOT, 'analysis', 'vxn.csv'))):
        try: V[row['date']] = float(row['vxn'])
        except ValueError: pass
    vk = sorted(V)
    rd = rules_daily()
    ret = {}; adj = [1.0]
    for k in range(1, len(dl)):
        d, p = dl[k], dl[k - 1]
        r = D[d]['c'] / D[d]['o'] - 1 if (d in R or p in R) else D[d]['c'] / D[p]['c'] - 1
        if abs(r) > 0.15: r = 0.0
        ret[d] = r; adj.append(adj[-1] * (1 + r))
    out = dict(era=ERA, variants={})
    rows = {name: dict(book=[], core=[]) for name in ('current', 'MA200', 'MA100', 'MA200-half')}
    for k in range(260, len(dl)):
        d, p = dl[k], dl[k - 1]
        i = bisect.bisect_left(vk, p)
        if i == 0: continue
        v = V[vk[i - 1]]; hist = sorted(V[x] for x in vk[max(0, i - 252):i]); med = hist[len(hist) // 2]
        w = min(1.5, med / v)
        c_prev = adj[k - 1]; ma200 = sum(adj[k - 200:k]) / 200; ma100 = sum(adj[k - 100:k]) / 100
        ws = {'current': w, 'MA200': w if c_prev > ma200 else 0.0, 'MA100': w if c_prev > ma100 else 0.0,
              'MA200-half': w if c_prev > ma200 else w / 2}
        for name, ww in ws.items():
            cr = ww * ret[d]; rows[name]['core'].append(cr); rows[name]['book'].append(cr + rd.get(d, 0.0))
    for name, x in rows.items():
        out['variants'][name] = dict(book=stats(x['book']), core=stats(x['core']),
                                     days_out_of_market=sum(1 for y, z in zip(x['core'], rows['current']['core']) if y == 0 and z != 0))
        print(name, out['variants'][name], flush=True)
    out['period'] = [dl[260], dl[-1]]
    json.dump(out, open(f'{A}/batch38_{ERA}.json', 'w'), indent=1)

main()
