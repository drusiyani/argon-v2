"""The market forecaster (Amendment 9): AI vs the market's own forecast. No AI, no API calls.

Fitted ONCE on Jul 2021 - Sep 2026 and then frozen: a logistic regression of 'is today a trend day?' (|close-open| >= 0.6 x range,
NQ 9:30-16:00) on two things known before the open: the VIX's 1-year percentile and yesterday's range vs its 20-day average.
Its size each morning comes from fixed cut-offs on the fitted probabilities: top 15% of days 2x, next 20% 1.5x, bottom 25% 0.5x, else 1x.
Writes research/results/market_forecaster.json (sha256 in PREREGISTRATION.md). Never re-fitted after the freeze."""
import os, sys, json, math, datetime as dt, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'engine'))
import portfolio as P, daytype
from zoneinfo import ZoneInfo
NY = ZoneInfo('America/New_York'); c = P.c
D, dl, _ = c.daily('NQ')
vix = {dt.datetime.fromtimestamp(t, NY).date().isoformat(): cl for t, o, h, l, cl in daytype.chart('%5EVIX', '10y', '1d')}
vk = sorted(vix); X, y, days = [], [], []
for k in range(21, len(dl)):
    d = dl[k]
    if not ('2021-07-01' <= d <= '2026-09-30'): continue
    rng = [D[dl[j]]['h'] - D[dl[j]]['l'] for j in range(k - 20, k)]; rr = rng[-1] / (sum(rng) / 20)
    prev = [v for v in vk if v < d]
    if len(prev) < 252: continue
    last = vix[prev[-1]]; window = [vix[v] for v in prev[-252:]]; pct = sum(1 for v in window if v <= last) / len(window)
    x = D[d]; rngd = x['h'] - x['l']
    if rngd <= 0: continue
    X.append([1.0, pct, rr]); y.append(1.0 if abs(x['c'] - x['o']) >= 0.6 * rngd else 0.0); days.append(d)
X, y = np.array(X), np.array(y); w = np.zeros(3)
for _ in range(50):                                            # Newton's method for logistic regression
    p = 1 / (1 + np.exp(-X @ w)); g = X.T @ (y - p); H = (X * (p * (1 - p))[:, None]).T @ X; w += np.linalg.solve(H, g)
p = 1 / (1 + np.exp(-X @ w)); q = np.quantile(p, [0.25, 0.65, 0.85])
brier = float(np.mean((p - y) ** 2)); base = float(np.mean((y.mean() - y) ** 2))
out = dict(written='2026-11-09', fitted_on=f'{days[0]} to {days[-1]} ({len(days)} days)', trend_day_rate=round(float(y.mean()), 3),
           coef=dict(intercept=round(float(w[0]), 4), vix_1y_percentile=round(float(w[1]), 4), range_ratio=round(float(w[2]), 4)),
           cutoffs=dict(half=round(float(q[0]), 4), one_and_half=round(float(q[1]), 4), two=round(float(q[2]), 4)),
           in_sample_brier=round(brier, 4), always_base_rate_brier=round(base, 4),
           size_rule='p >= two -> 2x; p >= one_and_half -> 1.5x; p < half -> 0.5x; else 1x',
           note='in-sample fit, so its live skill will likely be lower; it is a benchmark, not a strategy')
json.dump(out, open(os.path.join(ROOT, 'research', 'results', 'market_forecaster.json'), 'w'), indent=1); print(json.dumps(out, indent=1))
