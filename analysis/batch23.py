"""Batch 23 (14 Nov 2026). The test and its readings: analysis/BATCH23_PREREG.md (committed before this file ran).
Needs the batch 14 cache and analysis/_cache/batch23_lockbox2010.pkl (from batch23_dump.py)."""
import os, json, pickle
A = os.path.dirname(os.path.abspath(__file__))
exec(open(f'{A}/batch14.py').read().split('# ---- Part A')[0])
e = 'lockbox2010'; z = Z[e]; SB = pickle.load(open(f'{A}/_cache/batch23_{e}.pkl', 'rb'))
# ---- train once on the REAL book, 2018 onwards
train = [r for r in NQ if r['date'] >= '2018-01-01']; M = fit(np.array([r['f'] for r in train]), np.array([r['y'] for r in train]))
# ---- test on the scenario book before 2018
tr_s = [dict(t, id=('S', i)) for i, t in enumerate(SB['book_s'])]; TID = {t['id']: t for t in tr_s}
rows_s = rows24([t for t in tr_s if t['sym'] == 'NQ'], z['D'], z['atr'], z['on'], z['dl'], set(z['days']), z['w'])
test = [r for r in rows_s if r['date'] < '2018-01-01']; W = {r['id']: size(M, r['f']) for r in test}
def unseen(r): t = TID[r['id']]; return t['strat'] == 'quantlab' and t['date'] not in SB['real_days']['quantlab']
def groups(rows, val=lambda r: r['y']):
    out = {}
    for m_, lab in ((0.5, 'bottom'), (1.0, 'middle'), (1.5, 'top')):
        v = [val(r) for r in rows if W[r['id']] == m_]; out[lab] = dict(trades=len(v), avg_R=round(float(np.mean(v)), 3) if v else None)
    out['gap_top_minus_bottom'] = round(out['top']['avg_R'] - out['bottom']['avg_R'], 3) if (out['top']['avg_R'] is not None and out['bottom']['avg_R'] is not None) else None
    if out['gap_top_minus_bottom'] is not None:
        a = np.array([val(r) for r in rows if W[r['id']] == 1.5]); b = np.array([val(r) for r in rows if W[r['id']] == 0.5])
        out['t_stat'] = round(float((a.mean() - b.mean()) / np.sqrt(a.var() / len(a) + b.var() / len(b))), 2)
    return out
PER = (('2010-13', '2010', '2014'), ('2014-17', '2014', '2018'), ('2010-17', '2010', '2018'))
skill = {'all trades': {lab: groups([r for r in test if a <= r['date'] < b]) for lab, a, b in PER},
         'QuantLab never in the real book': {lab: groups([r for r in test if a <= r['date'] < b and unseen(r)]) for lab, a, b in PER},
         'QuantLab all': {lab: groups([r for r in test if a <= r['date'] < b and TID[r['id']]['strat'] == 'quantlab']) for lab, a, b in PER},
         'noise band + ATR band': {lab: groups([r for r in test if a <= r['date'] < b and TID[r['id']]['strat'] != 'quantlab']) for lab, a, b in PER}}
other_units = {'friction-free outcomes': {lab: groups([r for r in test if a <= r['date'] < b], lambda r: TID[r['id']]['free_R']) for lab, a, b in PER},
               'real outcomes': {lab: groups([r for r in test if a <= r['date'] < b], lambda r: TID[r['id']]['real_R']) for lab, a, b in PER}}
# ---- package over 2010-17 in the scenario
days = [d for d in E[e]['days'] if d < '2018-01-01']; di = {d: k for k, d in enumerate(days)}; core = E[e]['core']; risk = z['risk']
tt = [t for t in tr_s if t['date'] in di]; day = np.array([di[t['date']] for t in tt]); nr = np.array([t.get('w', 1.0) * (t['gross'] - t['cost']) for t in tt])
base = np.array([core[d] + z['tb'][d] for d in days]); sized = np.array([t['id'] in W for t in tt]); yr = np.array([int(t['date'][:4]) for t in tt])
mS = np.array([(0.0 if W.get(t['id']) == 0.5 else 1.0) for t in tt]); mH = np.array([(0.0 if W.get(t['id']) == 0.5 else W.get(t['id'], 1.0)) for t in tt])
def ret(w): return base + 0.5 * risk * np.bincount(day, weights=w * nr, minlength=len(days))
def full(r): x = list(r); return dict(metrics(x), boot=boot(x))
PKG = {'scenario package (fixed size)': full(ret(np.ones(len(tt)))), 'skip-only': full(ret(mS)), 'skip-and-press': full(ret(mH)), 'core only': full(base)}
b0, so = PKG['scenario package (fixed size)'], PKG['skip-only']
c_ok = bool(so['cagr_pct'] > b0['cagr_pct'] and so['sortino'] > b0['sortino'] and so['worst_drop_pct'] >= b0['worst_drop_pct'] - 1)
rng = np.random.default_rng(20261114); groups_y = [np.where(sized & (yr == y))[0] for y in sorted(set(yr[sized]))]; N = 5000
def cagr(r): return 100 * (np.prod(1 + r) ** (252 / len(r)) - 1)
luck = {}
for nm, m_ in (('skip-only', mS), ('skip-and-press', mH)):
    target = cagr(ret(m_)); hits = 0; tot = 0.0
    for _ in range(N):
        w = m_.copy()
        for g in groups_y: w[g] = w[g][rng.permutation(len(g))]
        v = cagr(ret(w)); hits += v >= target; tot += v / N
    luck[nm] = dict(model_return=round(float(target), 1), random_mean=round(float(tot), 1), random_beating=int(hits), draws=N, pct=round(100 * hits / N, 2))
a_ok = bool(all(skill['all trades'][lab]['gap_top_minus_bottom'] > 0 for lab in ('2010-13', '2014-17')))
b_ok = bool(all(skill['QuantLab never in the real book'][lab]['gap_top_minus_bottom'] > 0 for lab in ('2010-13', '2014-17')))
d_ok = bool(luck['skip-only']['pct'] < 5)
reading = "the model's skill carries to trades it has never seen" if (a_ok and b_ok and c_ok and d_ok) else ('the ranking carries, but is too weak to matter' if (a_ok and b_ok) else 'does not carry')
out = dict(train_rows=len(train), test_rows=len(test), test_unseen_quantlab=sum(1 for r in test if unseen(r)), share_of_test_by_group={k: int(sum(1 for r in test if W[r['id']] == k)) for k in (0.5, 1.0, 1.5)},
           skill=skill, other_units=other_units, package_2010_17=PKG, luck=luck, checks=dict(a=a_ok, b=b_ok, c=c_ok, d=d_ok), reading=reading)
json.dump(out, open(f'{A}/batch23.json', 'w'), indent=1, default=lambda o: o.item())
print('train', len(train), 'test', len(test), 'unseen QL', out['test_unseen_quantlab'], 'groups', out['share_of_test_by_group'])
for k, v in skill.items():
    for lab, g in v.items(): print(f"{k:34s} {lab}  bottom {g['bottom']}  middle {g['middle']}  top {g['top']}  gap {g['gap_top_minus_bottom']} t {g.get('t_stat')}")
for k, v in other_units.items():
    for lab, g in v.items(): print(f"{k:34s} {lab}  gap {g['gap_top_minus_bottom']} t {g.get('t_stat')}  (bottom {g['bottom']['avg_R']}, top {g['top']['avg_R']})")
for k, v in PKG.items(): print(k, v)
print(luck); print(out['checks'], '->', reading)
