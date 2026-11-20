"""Batch 34, part D (added after A-C ran; descriptive, not pre-registered): power of the desk's promotion rule.
Copied idea: NostroBenJ/intraday-strategy-replication runs its decision rule on pure noise and on planted edges.
Here: G3's rules sleeve, 2021-26 days. Windows of 120 and 230 consecutive trading days. Arms: 1x, the random sizer
(uniform 0.5/1/1.5/2), and an AI whose size tracks the day's result with skill rho (0 = none). Promotion rule
(Amendment 4): AI Sharpe on monthly R beats both other arms by >= 0.15."""
import os, json, math
import numpy as np
D = json.load(open('/tmp/g3_daily.json'))['databento']
r = np.array(D['g3']) - np.array(D['base'])          # rules sleeve of G3 (the part the desk sizes)
rng = np.random.default_rng(20261120); S = np.array([0.5, 1.0, 1.5, 2.0])
def sharpe_m(x):
    m = np.add.reduceat(x, np.arange(0, len(x), 21)); return m.mean() / (m.std(ddof=1) + 1e-12) * math.sqrt(12)
def auc(score, y):
    pos = score[y > 0]; neg = score[y <= 0]
    if len(pos) == 0 or len(neg) == 0: return np.nan
    return float((pos[:, None] > neg[None, :]).mean())
out = {}
for W in (120, 230):
    for rho in (0.0, 0.05, 0.1, 0.2):
        win = 0; aucs = []; gain = []
        for _ in range(3000):
            a = rng.integers(0, len(r) - W); x = r[a:a + W]
            z = (x - x.mean()) / (x.std() + 1e-12); s = rho * z + math.sqrt(1 - rho ** 2) * rng.standard_normal(W)
            ai = S[np.searchsorted(np.quantile(s, [.25, .5, .75]), s)]           # quartiles -> 0.5/1/1.5/2
            rnd = rng.choice(S, W); sa, s1, sr = sharpe_m(ai * x), sharpe_m(x), sharpe_m(rnd * x)
            win += (sa >= s1 + 0.15) and (sa >= sr + 0.15); aucs.append(auc(s, x)); gain.append(sa - s1)
        out[f'{W} days, skill {rho}'] = dict(promoted=round(win / 3000, 3), typical_AUC=round(float(np.nanmedian(aucs)), 3), median_sharpe_gain=round(float(np.median(gain)), 2))
        print(W, rho, out[f'{W} days, skill {rho}'], flush=True)
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'batch34_power.json'), 'w'), indent=1)

# alternative rule (Gemini's suggestion): shuffle the AI's own sizes across the days; promote only if its real total R
# beats 95% of the shuffles (same average size, so no credit for simply betting bigger)
alt = {}
for W in (120, 230):
    for rho in (0.0, 0.05, 0.1, 0.2):
        win = 0; n = 1000
        for _ in range(n):
            a = rng.integers(0, len(r) - W); x = r[a:a + W]
            z = (x - x.mean()) / (x.std() + 1e-12); s = rho * z + math.sqrt(1 - rho ** 2) * rng.standard_normal(W)
            ai = S[np.searchsorted(np.quantile(s, [.25, .5, .75]), s)]
            P = np.array([rng.permutation(ai) for _ in range(400)]); null = P @ x
            win += (ai @ x) > np.quantile(null, 0.95)
        alt[f'{W} days, skill {rho}'] = round(win / n, 3); print('shuffle test', W, rho, alt[f'{W} days, skill {rho}'], flush=True)
res = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'batch34_power.json')))
json.dump(dict(promotion_rule_plus015=res, shuffle_test_p05=alt), open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'batch34_power.json'), 'w'), indent=1)
