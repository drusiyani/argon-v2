# Batch 17 results (14 Nov 2026): the risk budget. Nothing inside Dru's limit reaches 80%

Pre-registration: `BATCH17_PREREG.md` (committed before the run). Code: `batch17.py`. Raw: `batch17.json`.
Each cell: return a year / Sharpe / worst drop / bootstrap chance of a drop worse than −35%.
Growth-mark limits: worst drop −24.4% and −28.5%; crash chance 35.3% and 8.3% (the Nasdaq alone).

| Scheme | Rules weight | 2021–26 | 2010–20 | Strict | Growth |
|---|---|---|---|---|---|
| Package today | 0.5 | +56.4% / 1.61 / −19.4% / 1.0% | +21.6% / 1.05 / −23.5% / 7.4% | — | — |
| Skip-only | 0.5 | +57.9% / 1.68 / −18.8% / 0.8% | +28.5% / 1.35 / −21.2% / 2.4% | yes | yes |
| Skip-only | 0.625 | +68.4% / 1.70 / −21.0% / 1.7% | +30.1% / 1.30 / −23.8% / 5.9% | no | yes |
| Skip-only | 0.75 | +79.1% / 1.71 / −23.2% / 5.1% | +31.7% / 1.25 / −26.4% / 13.5% | no | no |
| Skip-only | 0.875 | +89.9% / 1.70 / −25.5% / 10.8% | +33.2% / 1.19 / −29.0% / 29.1% | no | no |
| Skip-only | 1.0 | +101.0% / 1.68 / −28.2% / 19.7% | +34.5% / 1.14 / −31.7% / 47.0% | no | no |
| **Skip-and-press** | **0.5** | **+72.9% / 1.75 / −22.0% / 2.6%** | **+31.5% / 1.33 / −22.4% / 3.9%** | no | **yes** |
| Skip-and-press | 0.625 | +87.8% / 1.75 / −25.6% / 8.0% | +33.8% / 1.26 / −24.5% / 12.9% | no | no |
| Skip-and-press | 0.75 | +103.1% / 1.74 / −29.3% / 18.9% | +36.0% / 1.20 / −26.7% / 32.0% | no | no |
| Skip-and-press | 0.875 | +118.6% / 1.72 / −32.8% / 36.4% | +37.9% / 1.14 / −29.2% / 56.0% | no | no |
| Skip-and-press | 1.0 | +134.5% / 1.71 / −36.2% / 62.8% | +39.6% / 1.09 / −32.2% / 76.3% | no | no |

## Picks by the pre-registered rule
- **Same risk as today (strict mark):** skip-only at 0.5. +57.9% / +28.5%.
- **Dru's limit (growth mark):** skip-and-press at 0.5. +72.9% / +31.5%. It beats the batch 14 sizing (+72.3% / +28.1%) in
  both eras, with shallower drops and a lower 2010–20 crash chance (3.9% against 6.2%). Average trade size 1.00× and 0.91×.

## About 80%
Every configuration at or above 80% in 2021–26 fails the growth mark, each time because it becomes riskier than holding the
Nasdaq in 2010–20. The first one above 80 (skip-and-press at 0.625, +87.8%) has a 12.9% crash chance in 2010–20 against a
limit of 8.3%. It adds 15 points in the era the rules were picked on and 2.3 points in the sealed decade, while the sealed
decade's crash chance triples (3.9% → 12.9%). Sharpe is flat or falling as the weight rises: more weight is more risk, not more edge.
The marks were not moved.

## The pick in sub-periods (return a year / worst drop)

| | 2013–17 (rules had no edge) | 2018–20 | 2021–25 | 2026 so far |
|---|---|---|---|---|
| Package today | +9.5% / −23.5% | +53.9% / −20.4% | +64.2% / −19.4% | +19.1% / −18.9% |
| Skip-only, 0.5 | +15.8% / −20.8% | +66.7% / −19.5% | +64.3% / −18.8% | +25.9% / −18.7% |
| Skip-and-press, 0.5 | +15.1% / −22.4% | +82.1% / −21.1% | +80.7% / −20.6% | +35.0% / −22.0% |

Skip-and-press made about 80% a year in 2018–20 and 2021–25. The weaker 2026 pulls the whole 2021–26 figure down to 72.9%.

## Luck check (pick: skip-and-press at 0.5)
The same multipliers shuffled among each year's trades 300 times: average +54.5% (2021–26) and +21.9% (2010–20).
6 of 300 beat the model in 2021–26, 1 of 300 in 2010–20.

## Caveats
Skip-and-press was put together after seeing batches 14 and 16, so it is not blind. About 217 trials in total.
Backtest only; expect less live.
