# Batch 20 results (14 Nov 2026): how real are the findings?

Pre-registration: `BATCH20_PREREG.md` (committed before the run). Code: `batch20.py`. Raw: `batch20.json`. No new strategy.

## Part 1 — Search-luck test: "unlikely to be search luck" for both, but passing a mark alone means little
20,000 random rules each (the model's own sizes shuffled among each year's trades).

| | Skip-only | Skip-and-press |
|---|---|---|
| Model's return a year (2021–26 / 2010–20) | +57.9% / +28.5% | +72.9% / +31.5% |
| Average random rule | +47.7% / +21.3% | +55.0% / +21.8% |
| Random rules beating the model's return in BOTH eras | 1 of 20,000 | 0 of 20,000 |
| Chance the best of 230 random rules beats it in both eras | 1.1% (upper bound 3.4%) | under 3.4% |
| Random rules that PASS the same mark the model passed (no bootstrap part) | 233 of 20,000 (1.2%) | 1,601 of 20,000 (8.0%) |
| Chance at least one of 230 random rules passes that mark | 93% | 100% |

By the reading fixed in advance (under 5%), both are **unlikely to be search luck**: the two-era requirement is what does
the work, since a random rule beat skip-only in 2021–26 alone 445 times in 20,000.
The second finding matters as much: **passing a mark is weak evidence**. After about 230 tries, something would almost
certainly have passed the strict or growth mark by luck. What is rare is the size of the model's lead. The hand rules from
batches 11–12 (which only just passed, or just failed) deserve less weight than the model for this reason.
Limits: random shuffles are not the ~230 ideas actually tried, and this does not measure the hindsight in the feature list.

## Part 2 — Correction: QuantLab's direction in 2026 was right 58.6% of the time, not 65%
The 65% used the day's open-to-close move, which includes the candle that makes the signal. From the entry price to the close:

| Year | Old figure | From entry | Held to the close with no stop, avg R | Actual avg R (before costs) |
|---|---|---|---|---|
| 2018 | 58% | 53% | +1.40 | +0.07 |
| 2019 | 55% | 46% | +0.01 | +0.32 |
| 2020 | 60% | 53% | +0.80 | +0.09 |
| 2021 | 51% | 46% | −0.81 | +0.21 |
| 2022 | 61% | 55% | +0.34 | +0.14 |
| 2023 | 56% | 51% | −0.13 | +0.19 |
| 2024 | 58% | 50% | +0.11 | +0.35 |
| 2025 | 63% | 58% | +0.42 | +0.17 |
| 2026 | 65% | **59%** | **+1.41** | +0.08 |

2026 is still QuantLab's best year for direction, so the "right direction, stopped out first" reading survives, at a smaller
size. The no-stop column is in each trade's own R (a tight stop, so these positions would be far too big to hold without one);
it shows that in 2018 and 2026 the direction kept paying after the stop was hit, while in 2021 and 2023 the stop saved money.

## Part 3 — Costs in R terms, and a finding about the "sealed decade"
Average cost per momentum trade: 0.044–0.049R in 2010–13, 0.036–0.041R in 2015–19, 0.024R in 2020, 0.013–0.022R in 2021–25,
**0.010R in 2026**. The same 0.75 points costs about a quarter of what it did in 2011–14, because the index is ten times higher.

This exposed something not noticed before. QuantLab trades in the book per year: 2011 48, 2012 22, 2013 7, 2014 23, 2015 25,
2016 26, 2017 32, then 2018 170, 2019 148, 2020 228, and 121–238 a year since. QuantLab signals almost every day (about 240
a year), so **the cost rule removed 80–97% of QuantLab's trades before 2018**. Consequences:
- The 2010–17 results are mostly the noise band and ATR band. They say little about QuantLab, which is now the main engine
  (17.7 of the rules' 29.8 points a year in 2021–26).
- The "break in 2018" is partly the cost rule switching QuantLab on as the index and volatility rose, not only a change in
  the market. (Lockbox 2 did show QuantLab had no edge before costs over 2011–20 as a whole, so both things are true.)
- 2013–17 is not a clean picture of "what if the edge disappears in 2027": at today's index level the cost rule would not
  switch QuantLab off.
