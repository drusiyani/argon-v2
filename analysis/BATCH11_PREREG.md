# Batch 11 pre-registration (13 Nov 2026) — written and committed BEFORE the package test below was run

Analysis only (does not touch the race).

## Where this idea came from (read this first)
It was NOT blind. After batches 8–10 failed, Claude took the package apart trade by trade (attribution, no pass mark) and
looked at about eight trade attributes across three periods (2010–17, 2018–20, 2021–26). One stood out: trades taken in the
same direction as the overnight gap (today's 9:30 open vs yesterday's 16:00 close) did better than trades against it in all
three periods, for all three momentum rules (9 of 9 cells), and in 13 of 17 calendar years (8 of 8 in 2010–17).
Average result per trade, with the gap / against it: +0.02R / −0.13R (2010–17), +0.12R / +0.03R (2018–20), +0.15R / +0.05R (2021–26).
Because the pattern was found on this same data, a pass below is EXPECTED and is not independent proof. What the test adds
is the risk check at package level. The only clean test left is Race 1.

Why it could be real: the overnight move carries information that the day session keeps following (Gao et al. 2018 and
Baltussen et al. 2021 both use the return from the previous close, not from the open). A breakout against the gap is
a move back toward yesterday's close, where it tends to stall. The earlier "overnight reversal" test (fade the gap) lost money
in both eras, which is the same fact seen from the other side.

## K1 — Gap-direction reallocation
For QuantLab / noise band / ATR band trades: with the gap ×1.5, against the gap ×0.5 (on top of the usual 0.5). A zero gap
or a missing previous day ×1. Expiry trades unchanged. About 56% of trades are with the gap, so average size is about 1.06.

## K2 — Skip trades against the gap
Same trades: with the gap ×1, against the gap ×0. This only removes risk.

## Pass mark (same as batches 5–10)
ADOPT only if, in BOTH eras (2021–26 and 2010–20), vs the fixed package: higher per-year return AND higher Sortino AND worst
drop no more than 1 point deeper AND bootstrap chance of a drop worse than −35% no more than 1 point higher
(1,000 draws, 63-day blocks, seed 20261111).

## Extra checks, reported whatever they show
- The same comparison in three sub-periods (2010–17, 2018–20, 2021–26).
- If K1 or K2 passes: the leverage test from lever.py at 1.25× (worst drop shallower than −35% and under 20% of 21-day-block
  bootstraps below −35%, both eras). Reported, but NOT adopted on this evidence, because the idea was not blind.

## Not allowed after seeing results
No changing the multipliers, the definition of the gap, or the pass marks. A pass means "candidate for a shadow book in Race 1"
unless Dru openly adopts it as a flagged amendment.
