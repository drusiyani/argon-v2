# Batch 38 (23 Nov 2026): a trend filter on the Nasdaq core

Written before the run. Question: should the core only be held when the Nasdaq is in an uptrend?

**Variants (core only; the four rules unchanged):**
- current: weight w = min(1.5, median VXN over the past year / VXN), held close to close every day.
- MA200: same w, but only held when the previous close is above the 200-day average of closes (else 0).
- MA100: the same with a 100-day average.
- MA200-half: below the 200-day average, hold half of w instead of nothing.

Simplifications, the same for every variant: weight applied as a fraction of the account (no rounding to whole
contracts), no pre-FOMC leg, no T-bill interest. Roll days use open to close. Averages use roll-adjusted closes.

**Measured on both eras separately** (2011-2020, Jul 2021-Oct 2026): the main book (rules at 0.5% + core): return a year,
Sharpe, worst drop; and the core alone.

**Adopt a variant only if** it raises the book's Sharpe by at least 0.05 in BOTH eras and does not lower the return a
year by more than a quarter in either. Otherwise nothing changes. Four variants are added to the project's trial count.
