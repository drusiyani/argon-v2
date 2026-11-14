# Batch 13 results (14 Nov 2026): the growth mark, a walk-forward model, and stacks

Pre-registration: `BATCH13_PREREG.md` (committed before the run). Code: `batch13_dump.py`, `batch13.py`, `batch13_luck.py`.
Raw: `batch13.json`, `batch13_luck.json`.

**Growth mark (Dru's instruction):** better return and Sortino in both eras, worst drop no more than 5 points deeper than the
package, and never riskier than holding the Nasdaq alone (limits: −24.4% and −28.5% drop; crash chance 35.3% and 8.3%).
Each cell: return a year / Sortino / worst drop / bootstrap chance of a drop worse than −35%.

| | 2021–26 | 2010–20 | Strict mark | Growth mark |
|---|---|---|---|---|
| Package baseline | +56.4% / 3.18 / −19.4% / 1.0% | +21.6% / 1.75 / −23.5% / 7.4% | — | — |
| K1 gap direction (re-scored) | +65.7% / 3.46 / −20.5% / 2.6% | +27.8% / 2.08 / −20.7% / 4.0% | no | yes |
| M1 day-after reallocation (re-scored) | +70.3% / 3.58 / −24.2% / 2.2% | +30.1% / 2.26 / −25.0% / 6.6% | no | yes |
| M2 skip after a big win (re-scored) | +60.6% / 3.46 / −19.0% / 0.4% | +26.0% / 2.11 / −23.2% / 5.0% | yes | yes |
| M3 gap-and-yesterday (re-scored) | +63.5% / 3.41 / −20.3% / 1.0% | +27.2% / 2.11 / −20.0% / 4.5% | yes | yes |
| H3 vol-managed size (re-scored) | +65.2% / 3.51 / −19.9% / 1.2% | +23.6% / 1.92 / −22.5% / 8.7% | no | no (2010–20 crash chance above the index's 8.3%) |
| **W1 walk-forward ridge (new)** | **+71.5% / 3.64 / −22.2% / 1.2%** | **+26.8% / 2.08 / −24.4% / 6.9%** | no | **yes** |
| W2 walk-forward boosting (new) | +70.3% / 3.70 / −21.1% / 0.5% | +28.2% / 2.22 / −31.3% / 10.5% | no | no (2010–20 drop too deep) |
| Stack A = M1 × M2 × M3 (cap 2×) | +77.3% / 3.83 / −22.0% / 1.2% | +36.7% / 2.67 / −24.0% / 5.8% | no | yes |
| Stack C = Stack A × W1 (cap 2×) | +81.4% / 3.83 / −23.0% / 3.7% | +38.5% / 2.73 / −23.1% / 4.0% | no | yes |

Stack B was not built because H3 did not meet the growth mark alone.

## Which number to believe
- **Stack A and Stack C are inflated.** They multiply three rules that were found by scanning this same data, then scored on it.
- **W1 is the fairest number here.** Each year's sizes came from a model fitted only on earlier years (first model: 2013,
  trained on 677 trades). It never saw the year it sized. Trades it sized up vs down, average R after costs:
  2013–17 −0.02 vs −0.09; 2018–20 +0.19 vs −0.08; 2021–26 +0.17 vs −0.01. The order is right in all three periods.
- **Luck check (diagnostic):** shuffling W1's own sizes among each year's trades 300 times gave +59.4% a year on average in
  2021–26 (model: +71.5%) and +21.7% in 2010–20 (model: +26.8%). 2 of 300 shuffles beat the model in 2021–26 and 1 of 300 in
  2010–20. About 3 points of the 2021–26 gain is just extra size (average multiplier 1.11); the rest is choosing trades.
- **Caveat on W1:** the 24 features were chosen after the scans in batches 11–12, so the feature list has hindsight in it,
  even though the weights do not.

## Leverage (lever.py test at 1.25×): fails for every row
Lowest 2010–20 crash chance at 1.25× is 30.7% (M2); the limit is 20%.

## Bug fixed during the run
The first run kept the hand-rule multipliers for one era only, so the re-scored rows showed the baseline for 2021–26.
Fixed before any stack was built; the re-scored rows now match batches 11–12 exactly.
