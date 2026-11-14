# Batch 15 results (14 Nov 2026): why, what if we're wrong, and how much to bet

Pre-registration: `BATCH15_PREREG.md` (committed before the run). Code: `batch15_index.py`, `batch15.py`. Raw: `batch15.json`.

## Part A — Mechanism on the index itself (no rules involved)

**1. "A trend day is followed by a sideways day": NOT supported.** After the top fifth of days by move size, the next day's
move was bigger, not smaller, in every period and in both markets (Nasdaq: 0.51 vs 0.45, 0.56 vs 0.46, 0.50 vs 0.48 ATR).
Straightness the next day was about the same (higher in 2010–17, a little lower in 2018–20 and 2021–26). So the reason
Claude gave in batches 11–12 for the "day after a win is bad" pattern was wrong, and that pattern currently has no
explanation. A pattern with no explanation deserves less trust.

**2. "The day follows the overnight gap": true only when the gap goes against yesterday, and fading.**
Average open→close return in the gap's direction, basis points a day (t-statistic):

| | 2010–17 | 2018–20 | 2021–26 |
|---|---|---|---|
| Nasdaq, gap against yesterday | +5.8 (2.1) | +15.7 (2.4) | +1.7 (0.4) |
| Nasdaq, gap with yesterday | −1.8 (−0.7) | −11.5 (−1.9) | −0.9 (−0.2) |
| S&P, gap against yesterday | +5.0 (2.2) | +5.1 (1.0) | −0.4 (−0.1) |
| S&P, gap with yesterday | −0.4 (−0.2) | −7.4 (−1.4) | −3.4 (−1.0) |

The effect is real in 2010–20 in both markets, which supports the gap pattern. In 2021–26 it has almost gone on the Nasdaq
and gone on the S&P.

## Part B — Gap-continuation trade: FAIL (alone)
Condition met (positive in all three periods), so it was run. Alone at 1×: 2010–20 +6.7% a year, Sharpe 0.67;
2021–26 +3.6% a year, Sharpe 0.29 (needs 0.30). Not added to the package.

## Part C — Betting more on the model-sized rules: stays at 0.5
Each cell: return a year / Sharpe / worst drop / bootstrap chance of a drop worse than −35%.

| Rules weight | 2021–26 | 2010–20 | Growth mark |
|---|---|---|---|
| 0.5 (candidate) | +72.3% / 1.73 / −22.5% / 1.2% | +28.1% / 1.21 / −23.5% / 6.2% | yes |
| 0.75 | +101.8% / 1.72 / −30.3% / 16.6% | +30.5% / 1.05 / −28.2% / 40.8% | no |
| 1.0 | +132.3% / 1.68 / −37.5% / 58.5% | +32.2% / 0.93 / −32.9% / 86.0% | no |

In 2010–20, doubling the rules' weight adds 4 points of return and takes the crash chance from 6% to 86%. Sharpe falls in
both eras as the weight rises. More weight is more risk, not more skill.

## Part D — What if we are wrong? (return a year / worst drop)

| | 2013–17 (rules had no edge) | 2018–20 | 2021–25 | 2026 so far |
|---|---|---|---|---|
| Core only, no rules | +17.4% / −17.1% | +28.2% / −17.8% | +20.4% / −25.8% | +10.0% / −14.1% |
| Package today | +9.5% / −23.5% | +53.9% / −20.4% | +64.2% / −19.4% | +19.1% / −18.9% |
| Model-sized, rules 0.5 | +11.9% / −23.5% | +75.1% / −21.6% | +80.8% / −17.4% | +31.4% / −22.5% |
| Model-sized, rules 0.75 | +8.7% / −28.2% | +99.8% / −25.4% | +115.5% / −21.2% | +39.3% / −30.3% |
| Model-sized, rules 1.0 | +5.1% / −32.9% | +124.4% / −31.3% | +152.6% / −24.9% | +44.8% / −37.5% |

When the rules have no edge they cost the package about 8 points a year against holding the core alone, with a deeper drop.
Model sizing cuts that cost to about 5.5 points. When the edge is there, the rules add 25 to 60 points a year.
So the rules are a bet with a known price: roughly 6 to 8 points a year if the edge is gone, for as long as they stay switched on.
