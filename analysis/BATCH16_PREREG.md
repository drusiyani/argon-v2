# Batch 16 pre-registration (14 Nov 2026) — written and committed BEFORE any batch 16 code was run

Analysis only (does not touch the race). Dru asked for more adjustments WITHOUT increasing risk. That request has an exact
test: the original strict mark. So this batch is judged by the strict mark only, against the fixed package:
ADOPT-candidate only if, in BOTH eras (2021–26 and 2010–20): higher per-year return AND higher Sortino AND worst drop no more
than 1 point deeper AND bootstrap chance of a drop worse than −35% no more than 1 point higher
(1,000 draws, 63-day blocks, seed 20261111). About 205 trials so far.

## Checked first and dropped (already tested and rejected in round 1)
Caps on open trades: max 2 same-direction trades (P24), max 3 open trades (P25), skip or halve a trade opposing an open one
(P02, P03), noise band / ATR band overlap (V01, P01). Not re-run.

## The idea: use the batch 14 model only to take risk OFF
The walk-forward model (W1m: 24 features, ridge, refitted monthly on earlier trades only) so far sized trades ×0.5 / ×1 / ×1.5,
which raised average size to about 1.1× and failed the strict mark. Three versions that cannot add size:
- **R1 cut-only:** bottom third of predictions ×0.5, everything else ×1.
- **R2 skip-only:** bottom third ×0 (trade not taken), everything else ×1.
- **R3 size-neutral:** the model's ×0.5 / ×1 / ×1.5, divided by the average multiplier it gave to the previous 250 sized trades
  (needs 100, else divide by 1). Average size stays about 1×.
Expiry trades and anything the model has not sized stay ×1.

Not blind: batch 14 already showed the model's bottom-third trades average −0.11R, −0.11R and −0.01R in the three periods, so
a return gain from cutting them is expected. The open question is risk: the rules' short trades are the package's crash hedge
(long-only rules failed in batch 4), so cutting trades could deepen the package's drops even though it removes trades.

## If more than one passes
They are alternatives, not a stack. The one with the shallowest worst drop averaged over the two eras is the candidate.

## Not allowed after seeing results
No changing the thirds, multipliers, the 250/100 window, or the mark.
