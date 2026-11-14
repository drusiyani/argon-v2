"""Batch 21 (14 Nov 2026). Rules and marks: analysis/BATCH21_PREREG.md (committed before this file ran).
Step 2: reads the batch 14 cache and analysis/_cache/batch21_{era}.json from batch21_dump.py."""
import os, json, statistics
A = os.path.dirname(os.path.abspath(__file__))
exec(open(f'{A}/batch14.py').read().split('# ---- Part A')[0])
J = {e: json.load(open(f'{A}/_cache/batch21_{e}.json')) for e in ERAS}; LEG = {e: J[e]['leg_NQ'] for e in ERAS}
SO = {i: (0.0 if m == 0.5 else 1.0) for i, m in W1m.items()}
def series(e, mult=None, leg=0.0):
    z = E[e]['z']; risk = z['risk']; R = collections.defaultdict(float)
    for t in E[e]['tr']: R[t['date']] += (mult.get(t['id'], 1.0) if (mult is not None and mom(t) and t['sym'] == 'NQ') else 1.0) * net(t)
    return [E[e]['core'][d] + 0.5 * risk * R.get(d, 0.0) + leg * LEG[e].get(d, 0.0) + z['tb'][d] for d in E[e]['days']]
IDX = {e: [E[e]['z']['ret'][d] for d in E[e]['days']] for e in ERAS}; LIM = {e: dict(drop=metrics(IDX[e])['worst_drop_pct'], boot=boot(IDX[e])) for e in ERAS}
def full(x): return dict(metrics(x), boot=boot(x))
def compare(name, new, ref):
    out = {'name': name}
    for e in ERAS:
        h, b = full(new(e)), full(ref(e)); better = h['cagr_pct'] > b['cagr_pct'] and h['sortino'] > b['sortino']
        h['strict'] = bool(better and h['worst_drop_pct'] >= b['worst_drop_pct'] - 1 and h['boot'] <= b['boot'] + 1)
        h['growth'] = bool(better and h['worst_drop_pct'] >= b['worst_drop_pct'] - 5 and h['worst_drop_pct'] >= LIM[e]['drop'] and h['boot'] <= LIM[e]['boot']); h['ref'] = b; out[e] = h
    out['strict_both'] = out['databento']['strict'] and out['lockbox2010']['strict']; out['growth_both'] = out['databento']['growth'] and out['lockbox2010']['growth']; return out
# ---- mark 1: the leg alone at 1x notional
alone = {}
for e in ERAS:
    x = [LEG[e].get(d, 0.0) for d in E[e]['days']]; m = statistics.mean(x); sd = statistics.pstdev(x); tr = [LEG[e][d] for d in E[e]['days'] if d in LEG[e]]
    alone[e] = dict(days_traded=len(tr), per_year_pct=round(100 * m * 252, 1), sharpe=round(m / sd * 252 ** 0.5, 2), worst_drop_pct=metrics(x)['worst_drop_pct'], win_pct=round(100 * sum(v > 0 for v in tr) / len(tr), 1))
alone_pass = bool(all(alone[e]['per_year_pct'] > 0 and alone[e]['sharpe'] >= 0.3 for e in ERAS))
RES = {}
if alone_pass:
    RES['package + leg'] = compare('package + leg vs package', lambda e: series(e, None, 0.5), lambda e: series(e))
    RES['skip-only + leg'] = compare('skip-only + leg vs skip-only', lambda e: series(e, SO, 0.5), lambda e: series(e, SO))
# ---- diagnostics
def stat(v): m = statistics.mean(v); return dict(days=len(v), avg_bps=round(1e4 * m, 1), t=round(m / (statistics.pstdev(v) / len(v) ** 0.5), 2))
PER = (('2010-17', '2010', '2018'), ('2018-20', '2018', '2021'), ('2021-25', '2021', '2026'), ('2026', '2026', '2027'))
allNQ = {**J['lockbox2010']['leg_NQ'], **J['databento']['leg_NQ']}; allES = {**J['lockbox2010']['leg_ES'], **J['databento']['leg_ES']}
diag = dict(NQ={lab: stat([v for d, v in allNQ.items() if a <= d < b]) for lab, a, b in PER}, ES={lab: stat([v for d, v in allES.items() if a <= d < b]) for lab, a, b in PER},
            NQ_by_year={y: stat([v for d, v in allNQ.items() if d[:4] == y]) for y in sorted({d[:4] for d in allNQ})})
es3 = {lab: stat([v for d, v in allES.items() if a <= d < b]) for lab, a, b in (('2010-17', '2010', '2018'), ('2018-20', '2018', '2021'), ('2021-26', '2021', '2027'))}
replicates = bool(all(v['avg_bps'] > 0 for v in es3.values()))
corr = {}; ql_lost = {}
for e in ERAS:
    Rd = collections.defaultdict(float); Q = {}
    for t in E[e]['tr']:
        if mom(t) and t['sym'] == 'NQ': Rd[t['date']] += net(t)
        if t['strat'] == 'quantlab': Q[t['date']] = t['gross'] - t['cost']
    ds = [d for d in E[e]['days'] if d in LEG[e]]; a = [LEG[e][d] for d in ds]; b = [Rd.get(d, 0.0) for d in ds]; ma, mb = statistics.mean(a), statistics.mean(b)
    corr[e] = round(sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5, 3)
    lost = [LEG[e][d] for d in ds if d in Q and Q[d] < 0]; won = [LEG[e][d] for d in ds if d in Q and Q[d] > 0]
    ql_lost[e] = dict(leg_on_days_stopped_quantlab_lost=stat(lost) if lost else None, leg_on_days_it_won=stat(won) if won else None)
json.dump(dict(alone=alone, alone_passes=alone_pass, results=RES, sub_periods=diag, ES_three_periods=es3, ES_replicates=replicates, corr_with_rules=corr, vs_stopped_quantlab=ql_lost,
               cap_diag={**J['lockbox2010']['cap_diag'], **J['databento']['cap_diag']}), open(f'{A}/batch21.json', 'w'), indent=1)
print('ALONE', alone, 'pass', alone_pass)
for k, r in RES.items():
    for e in ERAS: h = r[e]; print(f"{k:18s} {e:12s} {h['cagr_pct']:5.1f} {h['sharpe']:4.2f} {h['sortino']:4.2f} {h['worst_drop_pct']:6.1f} {h['boot']:5.1f}  ref {h['ref']['cagr_pct']:5.1f} {h['ref']['sortino']:4.2f} {h['ref']['worst_drop_pct']:6.1f} {h['ref']['boot']:5.1f}  strict {h['strict']} growth {h['growth']}")
print('NQ', diag['NQ']); print('ES', diag['ES'], 'replicates', replicates, es3); print('corr', corr); print(ql_lost)
for y, v in diag['NQ_by_year'].items(): print(y, v)
