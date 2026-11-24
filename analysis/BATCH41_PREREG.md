# Batch 41 (24 Nov 2026): three strategies from social media, made mechanical

Written before the run. Two of the three were discretionary chart posts, so each is turned into one fixed rule here;
the result tests that rule, not the poster's judgement. All on NQ, one trade a day at most, 0.5% of the account at risk
(same sizing as Argon's rules), costs 1.1 NQ points per round trip, the cost rule (skip if costs > 0.1R), flat by 15:55,
if stop and target are hit in the same minute the stop counts. Roll days skipped.

1. **SMC break + fair value gap.** 5-minute bars from 08:00. Swing highs/lows = 5-bar pivots. Between 09:30 and 12:00,
   the first 5-minute close above the last unbroken swing high (below the last swing low) whose 3-bar window left a
   fair value gap (low[i] > high[i-2], or the mirror) arms a trade: limit entry at the middle of the gap within the next
   hour, stop at the last swing low (high), target 1.5R.
2. **Prior-day VWAP rejection.** Prior day's 09:30-16:00 average price (time-weighted: Argon's minute data carries no
   volume, so this stands in for VWAP). Between 09:45 and 11:30, the first 5-minute bar that trades through it and closes
   back on the far side is a rejection: short if it came from below, long if from above, only if NQ is weaker (for shorts)
   or stronger (for longs) than ES since 09:30. Entry at the next bar's open (market), stop beyond the bar's extreme, target 2R.
3. **Two-candle 4H sweep** (New York time). Candle A = 02:00-06:00, candle B = 06:00-10:00. Long if B's low is below A's
   low and B closes above A's high; short is the mirror. After 10:00, enter at the first touch of B's midpoint; target
   2x ATR, stop 4x ATR. Two ATR versions, both fixed now: (a) 14 five-minute bars, (b) 14 one-hour bars, before 10:00.

**Measured on both eras** (2011-2020, 2021-Oct 2026): trades, win rate, average R after costs, the strategy's own Sharpe,
and the rules book's (four rules, 0.5%) Sharpe / return a year / worst drop with it added as a fifth rule.
**Adopt only if** average R after costs is above 0 AND the rules book's Sharpe rises by at least 0.05, in BOTH eras.
Four trials added to the count.
