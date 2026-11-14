# Batch 23 pre-registration (14 Nov 2026) — written and committed BEFORE any batch 23 code was run

Analysis only (does not touch the race). One test, made possible by batch 22.

## Why this test exists
Batch 22 showed the cost rule removed about 90% of QuantLab's trades in 2010–17. No scan (batches 11–12) and no model
(batches 13–19) ever saw those trades. At today's friction they would all have been taken. That makes them a sample nobody
has looked at: in effect a third lockbox.

## The test
- **Train:** one ridge model (λ = 100, the same 24 features, standardised) on the REAL book's trades from 1 Jan 2018 to
  12 Nov 2026. Cut-points: thirds of its own training predictions. Fitted once.
- **Test:** every momentum trade of batch 22's today's-friction scenario book dated before 2018, with features computed
  from that scenario book. Outcome: the trade's R in the scenario.
- Groups by the trained cut-points: bottom third (skip), middle, top third (press).

## Readings fixed now
"The model's skill carries to trades it has never seen" only if ALL of:
(a) the top group's average R minus the bottom group's is above zero in BOTH 2010–13 and 2014–17, over all test trades;
(b) the same holds for QuantLab trades on days QuantLab was NOT in the real book (the cleanest unseen set);
(c) skip-only beats the scenario package over 2010–17 on return and Sortino, with a worst drop no more than 1 point deeper;
(d) fewer than 5% of 5,000 random rules (the model's sizes shuffled among each year's trades) beat skip-only's return.
If (a) and (b) hold but (c) or (d) fails → "the ranking carries, but is too weak to matter".
If (a) or (b) fails → "does not carry".
Also reported whatever it shows: skip-and-press; the middle group; and the same gaps measured on friction-free and on real
outcomes, to show whether the answer hinges on the scenario.

## Honest notes, stated now
- It is a backward test: trained on later years, tested on earlier ones. Nobody could have traded it. It asks whether what
  the model learned is a stable property of these trades.
- The feature list was chosen after scans that included 2010–17 noise band and ATR band trades (at real friction), so those
  are not clean. QuantLab's removed trades are.
- Outcomes are scenario outcomes (hypothetical friction).

## Not allowed after seeing results
No changing features, λ, cut-points, periods or readings.
