# Batch 40 (24 Nov 2026): five new ideas, tested together

Written before the run. None of these has been looked at on Argon's data before.

1. **Last half-hour momentum** (Gao, Han, Li & Zhou 2018): if NQ is up from 09:30 to 10:00 New York, go long at 15:30
   and exit at 16:00; if down, go short. 1x account notional.
2. **NQ-ES spread reversion:** at 11:00, d = NQ return since 09:30 minus ES return since 09:30. If |d| is more than
   1.5x its standard deviation over the previous 20 days at 11:00, short the leader and buy the laggard
   (1x notional each leg), exit 15:55.
3. **Turn of the month:** long NQ close to close on the last trading day of each month and the first three of the next.
   1x notional, on top of the existing core.
4. **Pre-holiday:** long NQ close to close on the trading day before a US market holiday (found from the data: the next
   weekday is not a trading day). 1x notional, on top of the core.
5. **Overnight-only core:** the existing core (same VXN weight) but held only from the 16:00 close to the next 09:30
   open, instead of close to close. This REPLACES the current core.

Costs: 2 ticks of slippage plus commission per round trip per contract (NQ about 1.1 points, ES about 0.75 points),
charged on every leg. Roll days are skipped for 1, 2 and 5 and use open-to-close for 3 and 4.
The book = the four rules at 0.5% per trade + the current core (Batch 38 method).

**Measured on both eras** (2011-2020, 2022-Oct 2026): each idea's own Sharpe after costs, its correlation with the book,
and the book's Sharpe, return a year and worst drop with the idea added (1-4) or swapped in (5).

**Adopt an idea only if** its own Sharpe after costs is above 0.3 in BOTH eras AND it raises the book's Sharpe by at
least 0.05 in BOTH eras without lowering the return a year by more than a quarter. Five trials added to the count.
