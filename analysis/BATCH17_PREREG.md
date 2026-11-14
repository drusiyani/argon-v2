# Batch 17 pre-registration (14 Nov 2026) — written and committed BEFORE any batch 17 code was run

Analysis only (does not touch the race). Dru asked for "at least 80" (% a year). A return number cannot be a search target:
looking until something shows 80 is how a backtest gets fooled. What can be done honestly is a RISK BUDGET: batch 16 showed
that skipping the model's worst third of trades lowers risk, so that saved risk can be spent on a bigger weight for the rules,
up to Dru's own limit (the growth mark from batch 13). No new patterns, no new scan. About 208 trials so far; this adds 9.

## The grid (fixed now)
Sizing scheme, both from the batch 14 model (W1m), nothing new fitted:
- **S skip-only:** bottom third not taken, everything else ×1 (batch 16's R2).
- **H skip-and-press:** bottom third not taken, middle ×1, top third ×1.5. This is R2 and the batch 14 sizing put together.
  It was chosen after seeing both results, so it is not blind.
Rules weight: 0.5 (today), 0.625, 0.75, 0.875, 1.0. Core, pre-FOMC and interest unchanged.

## Marks (unchanged)
- Strict mark: better return and Sortino, worst drop no more than 1 point deeper, crash chance no more than 1 point higher,
  both eras, against today's package.
- Growth mark: better return and Sortino, worst drop no more than 5 points deeper, and never riskier than the Nasdaq alone
  (worst drop and crash chance), both eras.

## Selection rule (fixed now)
- "Same risk as today" pick: among configurations meeting the STRICT mark, the one with the highest 2010–20 return.
- "Dru's limit" pick: among configurations meeting the GROWTH mark, the one with the highest 2010–20 return.
The sealed decade (2010–20) does the choosing on purpose, because 2021–26 is the era the rules were picked on.
Whether the pick reaches 80% in 2021–26 is reported as it falls. The marks will NOT be moved to reach 80.

## Reported for the picks
Sub-periods (2013–17 with no edge, 2018–20, 2021–25, 2026 so far) and the shuffle luck check.

## Not allowed after seeing results
No extra weights, no other multipliers, no changing the marks or the selection rule.
