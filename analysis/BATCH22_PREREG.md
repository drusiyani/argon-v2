# Batch 22 pre-registration (14 Nov 2026) — written and committed BEFORE any batch 22 code was run

Analysis only (does not touch the race). Dru asked Claude to look back over all the ideas and come up with better ones.
Reading the ~230 results together raised a doubt about a claim most of them were read through. This batch tests that claim.
No new strategy is tested.

## The claim under test
"The rules had no edge in 2010–17, even before costs" (Claude, batch 11; repeated since; given to the council as a fact).

## The doubt
The engine's "before costs" (gross) figures still include slippage in ticks: 1–2 ticks on entry, 1–3 on a stop, 1 on other
exits. A tick is 0.25 points at any index level. The Nasdaq future was near 2,300 in 2011 and is near 28,400 now, while
stops scale with the index. So the same ticks were a far larger share of each trade's risk in the early years. Batch 21
already showed the cost rule removed 80–97% of QuantLab's trades before 2018 for this reason.

## Part 1 — The same trades with no friction
For every picked trade of QuantLab, noise band and ATR band BEFORE the cost rule (monthly re-pick as in the real run):
its result with zero slippage and zero commission. Method: the same rule code is run again with tick slippage and commission
set to 0, and trades are matched by rule, date, variant and entry minute. Results are in units of the real trade's risk.
Reported by year and rule, for the Nasdaq and for the S&P, next to the real figures. Unmatched trades are counted and left out.
**Readings fixed now:**
- Nasdaq: the three rules' friction-free total positive in at least 6 of the 8 years 2010–17 → the claim is withdrawn and the
  2018 "break" is mainly friction. Positive in 3 or fewer → the claim stands. 4 or 5 → mixed.
- S&P: friction-free total positive in at least 12 of the 17 years 2010–26 → the rules' failure on the S&P is mainly friction.
  8 or fewer → the rules have no S&P edge even without friction. Otherwise mixed.

## Part 2 — Scenario: the same history at today's relative friction (a scenario, NOT history)
Each Nasdaq trade's result is moved from its real value towards its friction-free value in proportion to
(1 − entry price / 28,387.75), where 28,387.75 is the 12 Nov 2026 close; its commission is scaled by entry price / 28,387.75.
In plain words: slippage and commission are made the same share of price as they are today. The monthly re-pick is redone on
the adjusted trades and the cost rule is applied to the adjusted cost. The expiry rule, core, pre-FOMC tilt and interest are
unchanged. Rules weight 0.5, fixed size, no model.
Reported next to the real package: both eras, sub-periods (2010–17, 2018–20, 2021–25, 2026), and the rules' R by year.
- What it is for: an estimate of how the rules behave across 16 years of different markets at the friction they will face in 2027.
- What it is not: something that happened. It is not used to pass any mark or to argue for more size in this batch.
- Known bias, stated now: when friction was high nobody could trade this edge away; at today's friction anyone can. So the
  scenario probably overstates what the early years would really have paid.

## Not allowed after seeing results
No changing the 6-of-8 or 12-of-17 readings, the reference price, or the scenario's construction.
