"""Batch 17 (14 Nov 2026). Grid, marks and selection rule: analysis/BATCH17_PREREG.md (committed before this file ran)."""
import os, json, math, random
A = os.path.dirname(os.path.abspath(__file__))
exec(open(f'{A}/batch14.py').read().split('# ---- Part A')[0])
S = {i: (0.0 if m == 0.5 else 1.0) for i, m in W1m.items()}; H = {i: (0.0 if m == 0.5 else m) for i, m in W1m.items()}
def series(e, mult=None, rw=0.5):
    z = E[e]['z']; risk = z['risk']; R = collections.defaultdict(float)
    for t in E[e]['tr']: R[t['date']] += (mult.get(t['id'], 1.0) if (mult is not None and mom(t) and t['sym'] == 'NQ') else 1.0) * net(t)
    return [E[e]['core'][d] + rw * risk * R.get(d, 0.0) + z['tb'][d] for d in E[e]['days']]
IDX = {e: [E[e]['z']['ret'][d] for d in E[e]['days']] for e in ERAS}; LIM = {e: dict(drop=metrics(IDX[e])['worst_drop_pct'], boot=boot(IDX[e])) for e in ERAS}
B0 = {e: dict(metrics(series(e)), boot=boot(series(e))) for e in ERAS}
def score(name, mult, rw):
    out = {'name': name, 'rw': rw}
    for e in ERAS:
        x = series(e, mult, rw); h = dict(metrics(x), boot=boot(x)); b = B0[e]; better = h['cagr_pct'] > b['cagr_pct'] and h['sortino'] > b['sortino']
        h['strict'] = bool(better and h['worst_drop_pct'] >= b['worst_drop_pct'] - 1 and h['boot'] <= b['boot'] + 1)
        h['growth'] = bool(better and h['worst_drop_pct'] >= b['worst_drop_pct'] - 5 and h['worst_drop_pct'] >= LIM[e]['drop'] and h['boot'] <= LIM[e]['boot']); out[e] = h
    out['strict_both'] = out['databento']['strict'] and out['lockbox2010']['strict']; out['growth_both'] = out['databento']['growth'] and out['lockbox2010']['growth']; return out
RES = collections.OrderedDict(); RES['baseline'] = score('package today', None, 0.5); MULT = {'S': S, 'H': H}
for sc, lab in (('S', 'skip-only'), ('H', 'skip-and-press')):
    for rw in (0.5, 0.625, 0.75, 0.875, 1.0): RES[f'{sc}@{rw}'] = score(f'{lab}, rules weight {rw}', MULT[sc], rw)
grid = [k for k in RES if k != 'baseline']
def pick(flag): c = [k for k in grid if RES[k][flag]]; return max(c, key=lambda k: RES[k]['lockbox2010']['cagr_pct']) if c else None
P_strict, P_growth = pick('strict_both'), pick('growth_both')
SUBS = (('2013-17 (no edge)', 'lockbox2010', '2013', '2018'), ('2018-20', 'lockbox2010', '2018', '2021'), ('2021-25', 'databento', '2021', '2026'), ('2026 so far', 'databento', '2026', '2027'))
def sub(e, a, b, mult, rw):
    x = [v for v, d in zip(series(e, mult, rw), E[e]['days']) if a <= d < b]; m = metrics(x); return f"{m['cagr_pct']:+.1f}% / {m['worst_drop_pct']:.1f}%"
def detail(k):
    if not k: return None
    sc, rw = k.split('@'); rw = float(rw); mult = MULT[sc]; by = collections.defaultdict(list)
    for r in NQ:
        if r['id'] in mult: by[r['date'][:4]].append(r['id'])
    rng = random.Random(7); wins = {e: 0 for e in ERAS}; mean = {e: 0.0 for e in ERAS}
    for _ in range(300):
        sh = {}
        for y, ids in by.items(): v = [mult[i] for i in ids]; rng.shuffle(v); sh.update(zip(ids, v))
        for e in ERAS: c_ = metrics(series(e, sh, rw))['cagr_pct']; mean[e] += c_ / 300; wins[e] += c_ >= RES[k][e]['cagr_pct']
    avg = {e: round(sum(mult.get(t['id'], 1.0) for t in E[e]['tr'] if mom(t) and t['sym'] == 'NQ' and t['date'] in E[e]['ds']) / sum(1 for t in E[e]['tr'] if mom(t) and t['sym'] == 'NQ' and t['date'] in E[e]['ds']), 3) for e in ERAS}
    return dict(config=k, sub_periods={lab: sub(e, a, b, mult, rw) for lab, e, a, b in SUBS}, avg_multiplier=avg,
                luck={e: dict(shuffled_mean=round(mean[e], 1), shuffles_beating=wins[e]) for e in ERAS})
out = dict(limits_index_alone=LIM, results=RES, pick_same_risk_as_today=detail(P_strict), pick_dru_limit=detail(P_growth),
           baseline_sub_periods={lab: sub(e, a, b, None, 0.5) for lab, e, a, b in SUBS})
json.dump(out, open(f'{A}/batch17.json', 'w'), indent=1)
for k, r in RES.items():
    d, l = r['databento'], r['lockbox2010']
    print(f"{r['name'][:36]:36s} | {d['cagr_pct']:6.1f} {d['sharpe']:4.2f} {d['sortino']:4.2f} {d['worst_drop_pct']:6.1f} {d['boot']:5.1f} | {l['cagr_pct']:5.1f} {l['sharpe']:4.2f} {l['sortino']:4.2f} {l['worst_drop_pct']:6.1f} {l['boot']:5.1f} | strict {r['strict_both']} growth {r['growth_both']}")
print('limits', LIM); print('strict pick', json.dumps(out['pick_same_risk_as_today'])); print('growth pick', json.dumps(out['pick_dru_limit'])); print('baseline subs', out['baseline_sub_periods'])
