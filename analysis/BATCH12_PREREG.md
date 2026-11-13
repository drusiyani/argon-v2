# Batch 12 pre-registration (13 Nov 2026) — written and committed BEFORE the package tests below were run

Analysis only (does not touch the race).

## Where these ideas came from (read this first)
Not blind, same as batch 11. Claude fixed a list of 19 trade attributes, then compared them across three periods (2010–17,
2018–20, 2021–26). Two patterns held in all three periods and for all three momentum rules:

1. **The day after the rules lose is good; the day after they win is bad.** Rules' average result per day:
   after a losing day +0.02R / +0.40R / +0.31R; after a winning day −0.17R / −0.15R / +0.11R (the three periods in order).
   Better after a loss in 14 of 17 years. After a win of more than 2R the next day averaged −0.33R / −0.41R / −0.15R:
   negative in every period, including 2021–26. Day-level z-score 3.6 combined (19 attributes were scanned, so discount it).
   Blind support: batch 9's model, fitted separately on each era, gave a negative weight in BOTH eras to "rules' result over
   the previous 5 days" and to "yesterday's move".
2. **Gap and yesterday together.** The best trades go with today's overnight gap and against yesterday's direction
   (+0.08R / +0.17R / +0.18R); the worst go against the gap and with yesterday (−0.20R / +0.03R / +0.06R).

A likely reason for both: a strong trend day is usually followed by a sideways day, and breakout rules bleed on sideways days.
Because the patterns were found on this data, a pass is EXPECTED and is not independent proof. The clean test is Race 1.

Definitions: "yesterday's result" = total R after costs of the QuantLab / noise band / ATR band trades on the previous
trading day, from the unchanged book (no feedback from any resizing). All changes apply to those three rules' trades only.

## M1 — Day-after reallocation
Yesterday the rules lost → today's trades ×1.5. Yesterday they won → ×0.5. No trades yesterday → ×1.

## M2 — Skip the day after a big win (only removes risk)
Yesterday's result above +2R → no momentum trades today. The 2R is the bucket Claude looked at, not from a paper (flagged).

## M3 — Gap-and-yesterday reallocation (size-neutral)
Trade with the overnight gap AND against yesterday's open-to-close direction → ×1.5.
Trade against the gap AND with yesterday's direction → ×0.5. Everything else ×1.

## Pass mark (same as batches 5–11)
ADOPT only if, in BOTH eras (2021–26 and 2010–20), vs the fixed package: higher per-year return AND higher Sortino AND worst
drop no more than 1 point deeper AND bootstrap chance of a drop worse than −35% no more than 1 point higher
(1,000 draws, 63-day blocks, seed 20261111). Each idea alone. Ideas that pass alone are then combined and the combination
must pass the same mark.

## Reported, not adopted
For anything that passes: the 1.25× leverage numbers from lever.py's test. A pass means "candidate for a shadow book in
Race 1" unless Dru openly adopts it as a flagged amendment, because none of this was blind.

## Not allowed after seeing results
No changing multipliers, the 2R, definitions or pass marks.

## Addendum (13 Nov 2026, written after the Nasdaq package results, BEFORE the check below was run)
Replication on a market the scan never looked at: the same three rules, unchanged, on the S&P future (ES), costs 0.5 pts,
same 0.10R cost cap, both eras. The rules lose on the S&P overall, so only the DIFFERENCES matter:
- Day-after (M2): ES rules' average R per day on days after an ES result above +2R, vs all other days.
  Replicates if lower in all three periods (2010–17, 2018–20, 2021–26).
- Gap-and-yesterday (M3): average R per ES trade for "with the ES gap and against ES's yesterday" vs "against the gap and with
  yesterday". Replicates if higher in all three periods.
The S&P and Nasdaq move together on most days, so this is supporting evidence, not an independent proof. Reported whatever it shows.
