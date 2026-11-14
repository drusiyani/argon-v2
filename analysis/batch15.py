"""Batch 15 (14 Nov 2026). Rules and marks: analysis/BATCH15_PREREG.md (committed before this file ran).
Step 2: reads the batch 14 cache (trades, model features) and analysis/_cache/batch15_{era}.json from batch15_index.py."""
import os, json, math, statistics
A = os.path.dirname(os.path.abspath(__file__))
exec(open(f'{A}/batch14.py').read().split('# ---- Part A')[0])          # loads the caches and rebuilds the walk-forward models exactly as batch 14
IX = {e: json.load(open(f'{A}/_cache/batch15_{e}.json')) for e in ERAS}; GT = {e: IX[e]['gap_trade'] for e in ERAS}
PERS = (('2010-17', '2010', '2018'), ('2018-20', '2018', '2021'), ('2021-26', '2021', '2027'))
# ---- Part A: mechanism on the index itself
mech = {}
for S in ('NQ', 'ES'):
    rows = sorted(IX['lockbox2010']['days'][S] + IX['databento']['days'][S], key=lambda r: r['d']); mech[S] = {}
    for lab, a, b in PERS:
        R = [r for r in rows if a <= r['d'] < b]; cut = sorted(r['size'] for r in R)[int(0.8 * len(R))]
        aft = [(R[i + 1]['size'], R[i + 1]['eff']) for i in range(len(R) - 1) if R[i]['size'] >= cut]; oth = [(R[i + 1]['size'], R[i + 1]['eff']) for i in range(len(R) - 1) if R[i]['size'] < cut]
        def st(v):
            v = [x for x in v]; m = statistics.mean(v); return dict(days=len(v), avg_bps=round(1e4 * m, 1), t=round(m / (statistics.pstdev(v) / math.sqrt(len(v))), 2))
        ok = [r for r in R if not r['skip'] and r['g'] != 0]
        mech[S][lab] = dict(next_day_after_big_move=dict(size=round(statistics.mean(x for x, _ in aft), 3), straightness=round(statistics.mean(y for _, y in aft), 3)),
                            next_day_after_other=dict(size=round(statistics.mean(x for x, _ in oth), 3), straightness=round(statistics.mean(y for _, y in oth), 3)),
                            follow_gap_all=st([r['g'] * r['r'] for r in ok]), follow_gap_against_yesterday=st([r['g'] * r['r'] for r in ok if r['y'] != 0 and r['g'] != r['y']]),
                            follow_gap_with_yesterday=st([r['g'] * r['r'] for r in ok if r['g'] == r['y']]))
condB = all(mech['NQ'][lab]['follow_gap_against_yesterday']['avg_bps'] > 0 for lab, _, _ in PERS)
# ---- series with a rules-weight dial and the optional gap trade
def series(e, W=None, rw=0.5, k=1.0, gap=0.0):
    z = E[e]['z']; risk = z['risk']; R = collections.defaultdict(float)
    for t in E[e]['tr']: R[t['date']] += (W.get(t['id'], 1.0) if (W is not None and mom(t) and t['sym'] == 'NQ') else 1.0) * net(t)
    return [k * (E[e]['core'][d] + rw * risk * R.get(d, 0.0) + gap * GT[e].get(d, 0.0)) + z['tb'][d] for d in E[e]['days']]
IDX = {e: [E[e]['z']['ret'][d] for d in E[e]['days']] for e in ERAS}; LIM = {e: dict(drop=metrics(IDX[e])['worst_drop_pct'], boot=boot(IDX[e])) for e in ERAS}
B0 = {e: dict(metrics(series(e)), boot=boot(series(e))) for e in ERAS}
def score(name, **kw):
    out = {'name': name}
    for e in ERAS:
        x = series(e, **kw); h = dict(metrics(x), boot=boot(x)); b = B0[e]; better = h['cagr_pct'] > b['cagr_pct'] and h['sortino'] > b['sortino']
        h['growth'] = bool(better and h['worst_drop_pct'] >= b['worst_drop_pct'] - 5 and h['worst_drop_pct'] >= LIM[e]['drop'] and h['boot'] <= LIM[e]['boot']); out[e] = h
    out['growth_both'] = out['databento']['growth'] and out['lockbox2010']['growth']; return out
RES = collections.OrderedDict(); RES['baseline'] = score('package today (rules 0.5, fixed size)')
# ---- Part B
partB = dict(condition_met=bool(condB))
if condB:
    alone = {}
    for e in ERAS:
        x = [GT[e].get(d, 0.0) for d in E[e]['days']]; m = statistics.mean(x); sd = statistics.pstdev(x); tr = [GT[e][d] for d in E[e]['days'] if d in GT[e]]
        alone[e] = dict(trades=len(tr), per_year_pct=round(100 * m * 252, 1), sharpe=round(m / sd * math.sqrt(252), 2), worst_drop_pct=metrics(x)['worst_drop_pct'], avg_bps_per_trade=round(1e4 * statistics.mean(tr), 1))
    partB['alone_at_1x'] = alone; partB['alone_passes'] = bool(all(alone[e]['per_year_pct'] > 0 and alone[e]['sharpe'] >= 0.3 for e in ERAS))
    if partB['alone_passes']: RES['gap'] = score('package + gap-continuation trade (0.5x)', gap=0.5)
# ---- Part C: the dial
for rw in (0.5, 0.75, 1.0): RES[f'dial{rw}'] = score(f'model-sized rules at weight {rw}', W=W1m, rw=rw)
passing = [rw for rw in (0.5, 0.75, 1.0) if RES[f'dial{rw}']['growth_both']]; dial = max(passing) if passing else None
if 'gap' in RES and RES['gap']['growth_both'] and dial: RES['both'] = score(f'model-sized rules at {dial} + gap trade', W=W1m, rw=dial, gap=0.5)
# ---- Part D: what if we are wrong
def sub(e, a, b, **kw):
    x = [v for v, d in zip(series(e, **kw), E[e]['days']) if a <= d < b]; m = metrics(x); return f"{m['cagr_pct']:+.1f}% / {m['worst_drop_pct']:.1f}%"
SUBS = (('2013-17 (no edge)', 'lockbox2010', '2013', '2018'), ('2018-20', 'lockbox2010', '2018', '2021'), ('2021-25', 'databento', '2021', '2026'), ('2026 so far', 'databento', '2026', '2027'))
CH = collections.OrderedDict([('core only (no rules)', dict(rw=0.0)), ('package today', dict()), ('model-sized, rules 0.5', dict(W=W1m)), ('model-sized, rules 0.75', dict(W=W1m, rw=0.75)), ('model-sized, rules 1.0', dict(W=W1m, rw=1.0))])
partD = {nm: {lab: sub(e, a, b, **kw) for lab, e, a, b in SUBS} for nm, kw in CH.items()}
json.dump(dict(part_A_mechanism=mech, part_B=partB, results=RES, dial_chosen=dial, part_D_what_if_wrong=partD, limits_index_alone=LIM), open(f'{A}/batch15.json', 'w'), indent=1)
for S in mech:
    for lab in mech[S]: print(S, lab, json.dumps(mech[S][lab]))
print('PART B', json.dumps(partB))
for k, r in RES.items():
    d, l = r['databento'], r['lockbox2010']
    print(f"{r['name'][:42]:42s} | {d['cagr_pct']:6.1f} {d['sharpe']:4.2f} {d['sortino']:4.2f} {d['worst_drop_pct']:6.1f} {d['boot']:4.1f} | {l['cagr_pct']:5.1f} {l['sharpe']:4.2f} {l['sortino']:4.2f} {l['worst_drop_pct']:6.1f} {l['boot']:4.1f} | growth {r['growth_both']}")
print('dial chosen', dial)
for nm, v in partD.items(): print(f'{nm:26s}', v)
