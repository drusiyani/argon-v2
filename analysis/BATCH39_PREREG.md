# Batch 39 (23 Nov 2026): an intraday safety stop on the Nasdaq core

Written before the full run (only 20 and 23 Nov 2026 were looked at first, where a 2% stop would have saved ~$1,800).

**Variants (core only; rules unchanged):** if the Nasdaq trades S% below the previous close at any time before 16:00
New York (overnight session included), close the core at that price (fill: the stop or the bar's open if it gapped
through, minus 2 ticks) and re-buy at the 16:00 close. S = 1.5%, 2%, 3%. Plus the current core (no stop).
Same simplifications as Batch 38 (weight as a fraction of the account, no FOMC leg, no interest). Roll days: no stop.

**Measured on both eras** (2011-2020, Jul 2021-Oct 2026): the main book (rules at 0.5% + core): return a year, Sharpe,
worst drop; the core alone; how often the stop fired and how often the market then closed above the stop price.

**Adopt only if** it raises the book's Sharpe by at least 0.05 in BOTH eras and does not lower the return a year by more
than a quarter in either. Otherwise nothing changes. Three trials added to the count.
