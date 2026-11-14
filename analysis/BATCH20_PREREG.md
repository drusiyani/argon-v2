# Batch 20 pre-registration (14 Nov 2026) — written and committed BEFORE any batch 20 code was run

Analysis only (does not touch the race). Dru asked to look "even harder but smarter". After about 228 trials, another scan of
the same data would mostly find luck. So this batch tests no new strategy. It checks how real the existing findings are.

## Part 1 — Search-luck test (the only part with a decision reading)
20,000 random rules for each of skip-only and skip-and-press: the model's own multipliers shuffled among each year's sized
trades (same sizes, same counts per year, random trades). One random rule is applied to both eras.
Reported: the share of random rules that (a) beat the model's per-year return in BOTH eras; (b) pass the mark the model
passed (strict for skip-only, growth for skip-and-press; return, Sortino and worst-drop parts only, without the bootstrap
part, which makes passing EASIER for the random rules).
**Reading fixed now:** from (a), the chance that the best of 230 random rules would beat the model in both eras is
1 − (1 − p)^230. Under 5% → "unlikely to be search luck". 5% or more → "could be search luck".
Limits, stated now: random shuffles are not the same as the ~230 ideas actually tried, and this says nothing about the
hindsight in the model's feature list.

## Part 2 — Correction check (diagnostic)
On 14 Nov Claude told Dru that QuantLab "picked the day's direction right 65% of the time in 2026". That used the day's
open-to-close move, which includes the 9:30–9:35 candle that creates the signal. Recomputed from the entry price to the
close, by year, next to the old figure. Also reported: what each QuantLab trade would have made held to the close with no
stop, in its own R units, next to what it actually made.

## Part 3 — Costs in R terms (diagnostic)
Average cost per trade in R by year, 2010–2026. Costs are fixed in points while the index is about ten times higher than in
2010, so the same 0.75 points is a very different share of a trade's risk in each era.
