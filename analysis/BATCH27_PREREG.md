# Batch 27 pre-registration (15 Nov 2026) — written and committed BEFORE any batch 27 code was run

Analysis only (does not touch the race). One test: fixing G3's overconfidence (batch 26, Part 4 Risk 2). About 260 trials
so far; this adds 1.

## G3c — G3 with a recalibrated friction hurdle
- At the start of each month, offset = mean friction-free R − mean G3 prediction, over G3-judged trades dated in the previous
  12 months (needs 100 trades, else offset 0). Only trades dated before the month starts are used.
- Condition A (bottom third of the previous 252 raw predictions) is unchanged.
- Condition B becomes: (prediction + offset) − 1.25 / stop ≤ 0.
- Skip if A or B, as before.

## Expectation, stated now (Claude, 15 Nov)
Roughly the same backtest return; a few more skips in fading years (2013, 2016, 2026) and a few fewer in strong ones.

## Marks
STRICT mark against G3 in both eras (better return and Sortino, worst drop no more than 1 point deeper, crash chance no more
than 1 point higher), AND fewer than 5% of 5,000 random rules (G3c's skip decisions shuffled among each year's sized trades)
beat its return in both eras. If it fails, reported as insurance: sub-periods, extra skips and added trades by year,
and the offset by year.

## Not allowed after seeing results
No changing the 12-month window, the 100-trade minimum or the marks.
