"""Batch 32: faster-moving skip line. Rules: analysis/BATCH32_PREREG.md (committed before this file ran)."""
import os
A = os.path.dirname(os.path.abspath(__file__)); s29 = open(f'{A}/batch29.py').read()
exec(s29.split('# ---------------------------------------------------------------- U1')[0]); OUT = collections.OrderedDict(G3=REF)
RID = [r['id'] for r in rows]; STOP = np.array([FR[i][1] for i in RID])
def skips(win):
    G = {}; hist = []
    for k, r in enumerate(rows):
        if r['id'] not in PRED: continue
        p = PRED[r['id']]; a_ = len(hist) >= 100 and p < np.quantile(hist[-win:], 1 / 3); b_ = p - 1.25 / STOP[k] <= 0
        G[r['id']] = 0.0 if (a_ or b_) else 1.0; hist.append(p)
    return G
assert skips(252) == G3
GQ = skips(63); w = wfast(GQ); res = {e: full(ret2(e, w[e])) for e in ERAS}; judge('Q1_skip_line_63', res, luck(GQ))
SUB = (('2010-13', '2010', '2014'), ('2014-17', '2014', '2018'), ('2018-20', '2018', '2021'), ('2021-25', '2021', '2026'), ('2026', '2026', '2027'))
def sub(G):
    w = wfast(G); out = {}
    for lab, a, b in SUB:
        e = 'lockbox2010' if a < '2021' else 'databento'; m = np.array([a <= d < b for d in E[e]['days']]); out[lab] = round(cagr(ret2(e, w[e])[m]), 1)
    return out
s3, sq = sub(G3), sub(GQ); lvl = sum(sq[k] >= s3[k] - 0.1 for k in s3)
def month(G, m, k_=1.25):
    e = 'databento'; w = wfast(G)[e] * k_; r = ret2(e, w); ix = np.array([d.startswith(m) for d in E[e]['days']]); return round(100 * (float(np.prod(1 + r[ix])) - 1), 1)
# keep share per month under G3, and the changed trades split by month type
mon = collections.defaultdict(lambda: [0, 0]); TRD = {}
for e in ERAS:
    for k, t in enumerate(Q[e]['tr']):
        if Q[e]['mom'][k] and t['id'] in G3: m = E[e]['days'][Q[e]['day'][k]][:7]; mon[m][0] += 1; mon[m][1] += G3[t['id']]; TRD[t['id']] = (m, Q[e]['nr'][k])
hi = {m for m, v in mon.items() if v[0] >= 20 and v[1] / v[0] >= 0.85}
ch = [(i, GQ[i] - G3[i]) for i in G3 if GQ.get(i) != G3[i]]
def grp(f): L = [(d, TRD[i][1]) for i, d in ch if i in TRD and f(TRD[i][0])]; return dict(newly_skipped=sum(d < 0 for d, _ in L), newly_skipped_R=round(sum(r for d, r in L if d < 0), 1), newly_kept=sum(d > 0 for d, _ in L), newly_kept_R=round(sum(r for d, r in L if d > 0), 1))
OUT['Q1_skip_line_63'].update(sub_periods=dict(G3=s3, Q1=sq, level_or_better=int(lvl)), changed_share=round(len(ch) / len(G3), 3),
    changed_in_high_keep_months=grp(lambda m: m in hi), changed_in_other_months=grp(lambda m: m not in hi), july_2026_at_0625=dict(G3=month(G3, '2026-07'), Q1=month(GQ, '2026-07')),
    skip_share={e: round(1 - float(np.mean([GQ[i] for i in GQ if i[0] == e])), 3) for e in ERAS})
r = OUT['Q1_skip_line_63']; r['clears_noise_floor'] = bool(res['databento']['cagr_pct'] - REF['databento']['cagr_pct'] >= 3 and res['lockbox2010']['cagr_pct'] - REF['lockbox2010']['cagr_pct'] >= 1.5)
r['adopt'] = bool(r['adopt_candidate'] and r['clears_noise_floor'] and lvl >= 4)
json.dump(OUT, open(f'{A}/batch32.json', 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
print(json.dumps({k: r[k] for k in ('sub_periods', 'changed_share', 'changed_in_high_keep_months', 'changed_in_other_months', 'july_2026_at_0625', 'skip_share', 'clears_noise_floor', 'adopt')}, default=str))
