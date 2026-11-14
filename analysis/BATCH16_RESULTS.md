# Batch 16 results (14 Nov 2026): using the model only to take risk off passes the strict mark

Pre-registration: `BATCH16_PREREG.md` (committed before the run). Code: `batch16.py`, `batch16_checks.py`. Raw: `batch16*.json`.
Each cell: return a year / Sortino / worst drop / bootstrap chance of a drop worse than −35%.

| | 2021–26 | 2010–20 | Avg trade size | Strict mark |
|---|---|---|---|---|
| Package baseline | +56.4% / 3.18 / −19.4% / 1.0% | +21.6% / 1.75 / −23.5% / 7.4% | 1.00 | — |
| Model ×0.5 / ×1 / ×1.5 (batch 14) | +72.3% / 3.67 / −22.5% / 1.2% | +28.1% / 2.15 / −23.5% / 6.2% | 1.11, 1.04 | FAIL (2021–26 drop) |
| R1 cut-only (bottom third ×0.5) | +57.3% / 3.29 / −18.8% / 0.3% | +25.0% / 2.06 / −21.9% / 3.9% | 0.88, 0.87 | PASS |
| **R2 skip-only (bottom third not taken)** | **+57.9% / 3.30 / −18.8% / 0.8%** | **+28.5% / 2.29 / −21.2% / 2.4%** | 0.77, 0.73 | **PASS (candidate)** |
| R3 size-neutral | +67.7% / 3.60 / −20.5% / 0.7% | +27.7% / 2.14 / −23.5% / 5.6% | 1.00, 1.01 | FAIL by 0.1 (2021–26 drop −20.5%, limit −20.4%) |

R1 and R2 are the first changes in about 208 trials that raise return in both eras while lowering the worst drop and the
crash chance in both. By the pre-registered rule the candidate is R2 (shallowest drops). Sharpe: 1.61 → 1.68 and 1.05 → 1.35.

## The crash-hedge question
The skipped trades are 23–27% of all momentum trades and lean short (57–58% short, against 50% overall). They made +44R and
+66R on the core's worst 5% of days, about a sixth to a fifth of the rules' total hedge on those days. So skipping them does
give up some crash protection, but the package's drops still got shallower because the same trades lose on most other days.

## Sub-periods (return a year / worst drop)

| | 2013–17 (rules had no edge) | 2018–20 | 2021–25 | 2026 so far |
|---|---|---|---|---|
| Core only, no rules | +17.4% / −17.1% | +28.2% / −17.8% | +20.4% / −25.8% | +10.0% / −14.1% |
| Package today | +9.5% / −23.5% | +53.9% / −20.4% | +64.2% / −19.4% | +19.1% / −18.9% |
| Skip-only (R2) | +15.8% / −20.8% | +66.7% / −19.5% | +64.3% / −18.8% | +25.9% / −18.7% |
| Cut-only (R1) | +12.6% / −21.9% | +60.3% / −20.0% | +64.4% / −16.9% | +22.6% / −18.8% |
| Model ×0.5 / ×1 / ×1.5 | +11.9% / −23.5% | +75.1% / −21.6% | +80.8% / −17.4% | +31.4% / −22.5% |

The main effect is on the cost of being wrong. With no edge (2013–17) the package gave up 7.9 points a year against the core
alone; skip-only gives up 1.6. In 2021–25, when the edge was strong, skip-only made the same as the package (+64.3% vs +64.2%).

## Luck check (diagnostic)
Skipping the same number of trades each year at random, 300 times: average +47.3% (2021–26) and +21.3% (2010–20).
7 of 300 random versions beat skip-only on return in 2021–26, 0 of 300 in 2010–20.

## Caveats
- Not blind: batch 14 had already shown the bottom-third trades lose, so a return gain was expected. The risk result was not known.
- The model's 24 features were chosen after the batch 11–12 scans, so the feature list has hindsight in it. The weights do not.
- The model's first sizes are in 2013, so 2010–12 is unchanged in every row.
- Backtest only. Expect a smaller effect live.
