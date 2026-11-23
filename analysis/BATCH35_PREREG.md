# Batch 35 (23 Nov 2026): a minimum stop distance for Opening Drive

Written before the run. Prompted by 20 and 23 Nov 2026, when Opening Drive's stop sat a few points from the entry
(7.75 points on 23 Nov), the size was huge and normal noise stopped it out in the first minutes.

**Variants (Opening Drive only, everything else unchanged):** if the stop is closer than k x the 14-day average daily
range, either WIDEN it to k x range (fewer contracts, same 1R in dollars) or SKIP the trade. k = 0.02, 0.04, 0.06
(about 18, 35 and 53 points at today's ~880-point average range). 6 variants + the current rule.

**Measured on both eras separately** (2011-2020, Jul 2021-Oct 2026): the four-rule book at 0.5% per trade with the
cost rule, daily returns over all weekdays: Sharpe, total R, worst drop in R, and Opening Drive alone (trades, avg R).

**Adopt a variant only if** it raises the book's Sharpe in BOTH eras by at least 0.05 and does not raise the worst drop
by more than 10% in either. If several pass, take the one with the smallest k (least change). If none pass, nothing
changes. Two bad days are not evidence; seven variants are counted as seven more trials in the project's total.
