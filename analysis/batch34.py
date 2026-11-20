"""Batch 34 (20 Nov 2026): is G3 real once every test is counted? Rules: analysis/BATCH34_PREREG.md (committed before this ran).
Needs the same caches as batch 29. Uses purgedcv (MIT) for the deflated Sharpe and arch for the stationary bootstrap."""
import os, sys, glob, math
A = os.path.dirname(os.path.abspath(__file__)); s29 = open(f'{A}/batch29.py').read(); BAR = '# ---------------------------------------------------------------- '
exec(s29.split(BAR + 'the G3 pipeline')[0])
from statistics import NormalDist
from purgedcv import deflated_sharpe_ratio_full
from arch.bootstrap import StationaryBootstrap
Z = NormalDist().inv_cdf; OUT = collections.OrderedDict()

# ---- every distinct trial result saved so far, per era
seen = {'databento': {}, 'lockbox2010': {}}
def walk(o, path, f):
    if isinstance(o, dict):
        if isinstance(o.get('sharpe'), (int, float)):
            p = (f + '/' + '/'.join(path)).lower(); era = 'lockbox2010' if 'lockbox' in p or '2010' in p else ('databento' if 'databento' in p or '2021' in p else None)
            if era: seen[era][(round(o['sharpe'], 2), o.get('cagr_pct'))] = p           # identical results count once
        for k, v in o.items(): walk(v, path + [str(k)], f)
    elif isinstance(o, list):
        for i, v in enumerate(o): walk(v, path + [str(i)], f)
for f in sorted(glob.glob(f'{A}/*.json')):
    if os.path.basename(f).startswith('batch34'): continue
    try: walk(json.load(open(f)), [], os.path.basename(f))
    except Exception: pass
SH = {e: np.array([k[0] for k in seen[e]]) for e in ERAS}
print({e: (len(SH[e]), round(float(SH[e].var(ddof=1)), 4)) for e in ERAS}, flush=True)

g3 = {e: ret2(e, WG3[e]) for e in ERAS}; pkg = {e: ret2(e, np.ones(len(Q[e]['tr']))) for e in ERAS}
ann = lambda r: float(r.mean() / r.std(ddof=1) * math.sqrt(252))

# ---- Test A: deflated Sharpe
A_ = {}
for e in ERAS:
    A_[e] = {}
    for n in (299, 50):
        d = deflated_sharpe_ratio_full(g3[e], n_trials=n, var_sharpe=float(SH[e].var(ddof=1)), bars_per_year=252)
        A_[e][f'N={n}'] = dict(dsr=round(float(d.dsr), 4), sharpe_annual=round(ann(g3[e]), 2), luck_bar_annual=round(float(d.sr_star) * math.sqrt(252), 2))
    # family-only variance: trials within 0.6 of the package's Sharpe (the ones G3 was really picked from)
    fam = SH[e][np.abs(SH[e] - ann(pkg[e])) <= 0.6]
    d = deflated_sharpe_ratio_full(g3[e], n_trials=299, var_sharpe=float(fam.var(ddof=1)), bars_per_year=252)
    A_[e]['N=299, package family only'] = dict(trials_in_family=int(len(fam)), dsr=round(float(d.dsr), 4), luck_bar_annual=round(float(d.sr_star) * math.sqrt(252), 2))
    A_[e]['trials_seen'] = int(len(SH[e])); A_[e]['var_sharpe_annual'] = round(float(SH[e].var(ddof=1)), 4)
OUT['A_deflated_sharpe'] = A_; OUT['A_pass'] = bool(all(A_[e]['N=299']['dsr'] >= 0.95 for e in ERAS)); print('A', A_, flush=True)

# ---- Test B: G3 minus the package
def nw_t(x, L=5):
    x = np.asarray(x, float); n = len(x); u = x - x.mean(); g0 = u @ u / n; s = g0
    for l in range(1, L + 1): s += 2 * (1 - l / (L + 1)) * (u[l:] @ u[:-l]) / n
    return float(x.mean() / math.sqrt(s / n))
B_ = {}
for k, x in [(e, g3[e] - pkg[e]) for e in ERAS] + [('pooled', np.r_[g3['lockbox2010'] - pkg['lockbox2010'], g3['databento'] - pkg['databento']])]:
    bs = StationaryBootstrap(10, x, seed=20261120); mu = x.mean()
    draws = np.array([d[0][0].mean() for d in bs.bootstrap(10000)]) - mu                          # centred: the world where the gain is zero
    B_[k] = dict(days=int(len(x)), extra_return_pct_a_year=round(float(mu * 252 * 100), 2), t_newey_west=round(nw_t(x), 2),
                 bootstrap_p=round(float((draws >= mu).mean()), 4), days_better=round(float((x > 0).mean()), 3), days_worse=round(float((x < 0).mean()), 3))
OUT['B_gain_over_package'] = B_; OUT['B_bars'] = {'best of 299': round(Z(1 - 0.05 / 299), 2), 'best of 50': round(Z(1 - 0.05 / 50), 2)}
OUT['B_pass_299'] = bool(B_['pooled']['t_newey_west'] >= Z(1 - 0.05 / 299)); OUT['B_pass_50'] = bool(B_['pooled']['t_newey_west'] >= Z(1 - 0.05 / 50))
print('B', B_, OUT['B_bars'], flush=True)

# ---- Test C: each rule before / after 1 May 2024 (2021-26 era; the paper's rule is the noise band)
C_ = {}
q = Q['databento']; days = E['databento']['days']
for st in sorted(set(q['strat'])):
    m = np.array([s_ == st for s_ in q['strat']]); C_[st] = {}
    for lab, ok in (('before May 2024', lambda d: d < '2024-05'), ('from May 2024', lambda d: d >= '2024-05')):
        ix = [i for i in np.where(m)[0] if ok(q['tr'][i]['date'])]; r = q['nr'][ix]
        if len(r) < 5: continue
        byday = collections.defaultdict(float)
        for i in ix: byday[q['tr'][i]['date']] += q['nr'][i]
        top = sorted(byday.values(), reverse=True)[:10]; tot = sum(byday.values())
        C_[st][lab] = dict(trades=int(len(r)), mean_R=round(float(r.mean()), 3), t=round(float(r.mean() / r.std(ddof=1) * math.sqrt(len(r))), 2),
                           total_R=round(float(r.sum()), 1), best10_days_share=round(top and sum(top) / tot, 2) if tot > 0 else None)
OUT['C_rules_before_after_publication'] = C_
nb = C_.get('noiseband', {}).get('from May 2024', {}); OUT['C_flag_noiseband'] = bool(nb and (nb['mean_R'] <= 0 or nb['t'] < 1))
print('C', json.dumps(C_, indent=1), flush=True)
json.dump(OUT, open(f'{A}/batch34.json', 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
