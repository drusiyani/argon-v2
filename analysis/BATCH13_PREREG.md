# Batch 13 pre-registration (14 Nov 2026) — written and committed BEFORE any batch 13 code was run

Analysis only (does not touch the race).

## Change of pass mark, at Dru's instruction (14 Nov 2026)
Dru: "deeper drops is fine as long as it doesn't go too much", and keep looking. So from this batch on, ideas are judged by
the **growth mark**. An idea meets it only if, in BOTH eras (2021–26 and 2010–20), against the fixed package:
1. higher per-year return AND higher Sortino; and
2. worst drop no more than **5 points** deeper than the package's (limits: −24.4% and −28.5%); and
3. never riskier than just holding the Nasdaq in that era: worst drop no deeper than the index's (−35.1%, −28.6%) and
   bootstrap chance of a drop worse than −35% no higher than the index's (35.3%, 8.3%; 1,000 draws, 63-day blocks, seed 20261111).

Honest notes on this change:
- The "5 points" is Claude's reading of "not too much". Claude had already seen earlier results when choosing it (for example
  M1's −24.2%), so re-scoring OLD ideas under the new mark is after-the-fact and is labelled that way. Dru can change the 5.
- The old strict mark is still reported next to the new one for every result.
- Trial count is about 190 and the last two batches were found by scanning this data. Backtest gains from stacking such
  ideas are inflated. The fairest number in this batch is the walk-forward one (Part B), which only ever uses the past.

## Part A — Re-score earlier ideas under the growth mark (no new strategy)
K1, M1, M2, M3 (batches 11–12) and H3 (batch 9), recomputed from the same definitions. Labelled "re-scored".

## Part B — Walk-forward learned sizing (the new test)
Question: could a model have found and used these patterns in real time, knowing only the past?
- Unit: every QuantLab / noise band / ATR band trade, 2010–2026. Target: its R after costs.
- Features, fixed now, ALL of them used (no picking), each known at entry: gap direction vs trade; |gap|/ATR; signed gap/ATR;
  yesterday's open-to-close vs trade; yesterday's close-to-close vs trade; 5-day and 20-day move vs trade; open outside
  yesterday's range (with/against); yesterday's close location vs trade; yesterday's range/ATR; yesterday's rules result
  (capped ±5R); no trades yesterday; VXN core weight; side; rule (2 flags); time of day; stop size/ATR; same-direction
  trades already open; trade number that day; agreement with that day's QuantLab side; Monday; where the open sits in the
  overnight range vs trade; the rules' result so far that day (capped ±3R). 24 features.
- At the start of each calendar year the model is refitted on ALL trades from earlier years only (needs ≥ 500). It then sizes
  that year's trades: prediction in the bottom third of its training predictions ×0.5, middle ×1, top ×1.5. Before a model
  exists ×1. Expiry trades ×1.
- W1: ridge regression, λ = 100, features standardised on the training set.
- W2: gradient boosting (scikit-learn HistGradientBoostingRegressor, max_depth 3, 200 rounds, learning rate 0.03,
  min 100 trades per leaf, seed 0). Fixed now, not tuned.
- Judged by the growth mark (strict mark also shown).

## Part C — Stacks (only from parts that meet the growth mark alone)
- Stack A = product of the multipliers of those of M1, M2, M3 that meet the growth mark alone. K1 is left out because M3
  already uses the gap. A trade's total multiplier is capped at 2.0 (the same top size Dru set for the AI desk).
- Stack B = Stack A with H3's volatility-managed size on top (if H3 meets the growth mark alone).
- Stack C = Stack A × the walk-forward model's multiplier (W1 if it meets the mark, else W2 if it does), same 2.0 cap.
Each stack must itself meet the growth mark. Reported for each: the lever.py test at 1.25× (worst drop shallower than −35% and
under 20% of 21-day-block bootstraps below −35%, both eras).

## Not allowed after seeing results
No changing features, λ, model settings, multipliers, the cap, the 5 points, or which parts go into which stack.
