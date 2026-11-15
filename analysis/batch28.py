"""Batch 28 (15 Nov 2026). Candidates and selection rule: analysis/BATCH28_PREREG.md (committed before this file ran)."""
import os, json, math
from scipy import stats as sst
A = os.path.dirname(os.path.abspath(__file__))
src24 = open(f'{A}/batch24.py').read()
exec(src24.split('# ---- vectorised package returns per era')[0])
exec(src24.split('# ---- vectorised package returns per era')[1].split('ELIG = {')[0])
TD = sorted(set(d for e in ERAS for d in E[e]['z']['dl']))
TR = {t['id']: t for e in ERAS for t in E[e]['tr']}
kept = sorted([TR[i] for i, m in G3.items() if m == 1.0], key=lambda t: (t['date'], t['entry_min'])); kr = {t['id']: net(t) for t in kept}
dR = collections.defaultdict(float)
for t in kept: dR[t['date']] += kr[t['id']]
days = [d for d in TD if d >= kept[0]['date']]; x = np.array([dR.get(d, 0.0) for d in days])
def psr(v):
    sd = v.std()
    if sd == 0: return 0.5
    sr = v.mean() / sd; g3 = sst.skew(v); g4 = sst.kurtosis(v, fisher=False); den = 1 - g3 * sr + (g4 - 1) / 4 * sr * sr
    return float(sst.norm.cdf(sr * math.sqrt(len(v) - 1) / math.sqrt(max(den, 1e-9))))
P252, P126 = {}, {}
for k, d in enumerate(days):
    if k + 1 >= 252: P252[d] = psr(x[k - 251:k + 1]); P126[d] = psr(x[k - 125:k + 1])
def k2():
    w = 1.0; out = {}
    for d in days:
        out[d] = w
        if d in P252:
            p, q = P252[d], P126[d]
            if w == 0.0: w = 0.5 if (p >= 0.5 or q >= 0.85) else 0.0
            else: w = 1.0 if p >= 0.8 else (0.5 if p >= 0.5 else 0.0)
    return out
def k2g():
    w = 1.0; out = {}
    for d in days:
        out[d] = w
        if d in P252:
            p, q = P252[d], P126[d]
            if p >= 0.80 or (w < 1.0 and q >= 0.85): w = 1.0
            elif p >= 0.50: w = 0.5
            else: w = 0.0
    return out
# B: needs the package's own path; computed per era, day by day
def wB():
    out = {}
    for e in ERAS:
        z = E[e]['z']; risk = z['risk']; yr = None
        for d in E[e]['days']:
            if d[:4] != yr: yr = d[:4]; w = 1.0; eq = peak = 1.0; sh = shpk = 0.0
            out[d] = w
            r = E[e]['core'][d] + z['tb'][d] + 0.5 * risk * w * dR.get(d, 0.0); eq *= 1 + r; peak = max(peak, eq)
            sh += dR.get(d, 0.0); shpk = max(shpk, sh)
            if eq / peak - 1 <= -0.22 or shpk - sh > 30: w = 0.0
            elif w == 1.0 and eq / peak - 1 <= -0.15: w = 0.5
    return out
DW = {'K2 (batch 26)': k2(), "K2g (Gemini's T12 spec)": k2g(), 'B drawdown rule': wB()}
def M_of(dw): return {i: m * dw.get(TR[i]['date'], 1.0) for i, m in G3.items()}
REF = {e: full(ret(e, wvec(e, G3))) for e in ERAS}
SUB = (('2010-13', 'lockbox2010', '2010', '2014'), ('2014-17', 'lockbox2010', '2014', '2018'), ('2018-20', 'lockbox2010', '2018', '2021'), ('2021-25', 'databento', '2021', '2026'), ('2026', 'databento', '2026', '2027'))
def subs(M):
    out = {}
    for lab, e, a, b in SUB:
        r = ret(e, wvec(e, M)); seg = [v for v, d in zip(r, E[e]['days']) if a <= d < b]; m = metrics(seg); out[lab] = (m['cagr_pct'], m['worst_drop_pct'])
    return out
worst = {}
for e in ERAS:
    ds = E[e]['days']; c_ = sorted(ds, key=lambda d: E[e]['core'][d]); worst[e] = set(c_[:len(ds) // 20])
RES = collections.OrderedDict(); RES['G3, no switch'] = dict(result=REF, sub=subs(G3), worse_era_sortino=min(REF[e]['sortino'] for e in ERAS))
for nm, dw in DW.items():
    M = M_of(dw); h = {e: full(ret(e, wvec(e, M))) for e in ERAS}
    share = {lab: {str(w): round(float(np.mean([dw.get(d, 1.0) == w for d in days if a <= d < b])), 3) for w in (1.0, 0.5, 0.0)} for lab, _, a, b in SUB}
    cut_on_worst = {e: int(sum(1 for d in worst[e] if dw.get(d, 1.0) < 1.0 and dR.get(d, 0.0) != 0.0)) for e in ERAS}
    rules_R_lost_on_worst = {e: round(float(sum((1 - dw.get(d, 1.0)) * dR.get(d, 0.0) for d in worst[e])), 1) for e in ERAS}
    RES[nm] = dict(result=h, strict_vs_G3=bool(all(strict(h[e], REF[e]) for e in ERAS)), worse_era_sortino=min(h[e]['sortino'] for e in ERAS),
                   sub=subs(M), weight_share=share, weight_13_nov_2026=dw.get(days[-1]), cut_on_core_worst_5pct_days=cut_on_worst, rules_R_given_up_on_core_worst_days=rules_R_lost_on_worst)
cands = [k for k in DW]; best = max(cands, key=lambda k: RES[k]['worse_era_sortino'])
ties = [k for k in cands if RES[best]['worse_era_sortino'] - RES[k]['worse_era_sortino'] <= 0.02]
if len(ties) > 1: best = max(ties, key=lambda k: RES[k]['sub']['2021-25'][0])
beats_no_switch = RES[best]['worse_era_sortino'] > RES['G3, no switch']['worse_era_sortino']
daily_sd = float(np.std([dR.get(d, 0.0) for d in days]))
out = dict(results=RES, chosen=best, chosen_beats_no_switch_on_worse_era_sortino=bool(beats_no_switch), g3_rules_daily_R_sd=round(daily_sd, 3))
json.dump(out, open(f'{A}/batch28.json', 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
fmt = lambda h: f"{h['cagr_pct']:5.1f} {h['sortino']:4.2f} {h['worst_drop_pct']:6.1f} {h['boot']:5.1f}"
for nm, r in RES.items():
    print(f"{nm:26s}", ' | '.join(fmt(r['result'][e]) for e in ERAS), '| worse-era Sortino', r['worse_era_sortino'], '| strict', r.get('strict_vs_G3'))
    print('    sub', r['sub']); [print('   ', k, r[k]) for k in ('weight_share', 'weight_13_nov_2026', 'cut_on_core_worst_5pct_days', 'rules_R_given_up_on_core_worst_days') if k in r]
print('CHOSEN', best, '| beats no switch on worse-era Sortino:', beats_no_switch, '| G3 rules daily R sd', round(daily_sd, 3))
