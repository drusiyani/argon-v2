"""Pre-registers what "consistent with the backtest" means for the live book (Amendment 6, council point 7).

For k = 1..12 months: every rolling k-month sum of the book's monthly R (V4, 1x costs, Jul 2021 - Sep 2026, from
data/portfolio.json), and its 5th, 50th and 95th percentiles. Live: after k finished months, the live R so far (in rule R,
every trade the rules took, including ones too small for a micro) is compared with the k-month band.
It is a FLAG, not a stop rule. The backtest is mostly in-sample, so this band is optimistic.
Written once, 2 Nov 2026; its sha256 is in PREREGISTRATION.md. Never re-run after the freeze."""
import os, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = json.load(open(os.path.join(ROOT, 'data', 'portfolio.json')))
months = []; y, m = 2021, 7
while (y, m) <= (2026, 9): months.append(f'{y}-{m:02d}'); m += 1; y += m > 12; m = (m - 1) % 12 + 1
first = P['window'][0]; assert first == '2021-07'
R = P['main']['monthly_R'][:len(months)]; assert len(R) == 63
def pct(xs, q):
    xs = sorted(xs); i = (len(xs) - 1) * q; lo = int(i); hi = min(lo + 1, len(xs) - 1); return round(xs[lo] + (xs[hi] - xs[lo]) * (i - lo), 2)
bands = {}
for k in range(1, 13):
    sums = [sum(R[i:i + k]) for i in range(len(R) - k + 1)]
    bands[str(k)] = dict(p5=pct(sums, .05), p50=pct(sums, .5), p95=pct(sums, .95), n=len(sums))
out = dict(rule='after k finished live months, live rule-R so far must sit inside the backtest\'s 5th-95th percentile of rolling k-month sums',
           source='data/portfolio.json main.monthly_R, Jul 2021 - Sep 2026 (63 months), V4, 1x costs', written='2026-11-02',
           note='flag only, never a stop rule; the backtest is mostly in-sample, so the band is optimistic', bands=bands)
p = os.path.join(ROOT, 'research', 'results', 'live_band.json'); json.dump(out, open(p, 'w'), indent=1)
print(json.dumps(bands))
