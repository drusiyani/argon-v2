# Batch 40 (24 Nov 2026): TikTok strategy sweep (@thequantbuilder, 67 videos)

Written before the first run. Rules are fixed here; no tuning after seeing results.
Source: 67 short videos Dru supplied. Most are history, psychology or promotion. The ones with a rule that fits our
1-minute NQ/ES data are tested below, one fixed version each. The creator sells algos; none of his numbers are trusted,
we only test the rules.

**Data:** NQ and ES 1-minute bars (same loaders as batches 35-39), resampled to 5-minute and 1-hour. Two eras:
Jul 2021-Dec 2024 (`databento`) and 2011-2020 (`lockbox2010`). `ARGON_FULL` is NOT set, so 2025 onward stays sealed.
Roll sessions are dropped. Costs: `common.COST` per round trip (NQ 0.75 pt, ES 0.5 pt), taken off every trade.
Output is summary numbers only (counts, win rate, mean R, percentile vs random). No bars leave the runner.

**Common exit:** stop as stated, otherwise exit at the time stated. Stop and target in the same bar = stop first.
Gap through the stop fills at the open. R = net points / stop distance.

## Tests (NQ and ES unless noted)
5-minute series, entry at the open of the 09:35 bar (the first candle has just closed), exit 15:55 bar close:
1. **Candle momentum:** first 5-min candle (09:30) closes above its 12-period EMA (5-min closes, whole series) -> long, below -> short. Stop 0.5 x daily ATR(14). (Video adds a trailing stop and multi-day holds; not copied.)
2. **First-candle direction:** green first candle -> long, red -> short. Same stop.
3. **Always long** and **always short** at 09:35 (reported as reference only, no random test).
4. **Larry Williams range break:** day open +/- 0.5 x previous day's range; the first 5-min bar that touches a level
   (skip if both) triggers; enter at the next bar's open in that direction; stop 0.5 x previous range; exit 15:55 close.

1-hour series, signal at a bar's close, entry at the next bar's open, stop 1.5 x ATR(14 hourly bars), fixed hold:
5. **EMA cross:** EMA20 crosses EMA50 (up = long, down = short), hold 4 bars.
6. **MACD cross:** MACD(12,26,9) line crosses signal, hold 4 bars.
7. **SuperTrend flip:** (10, 3) flip, hold 4 bars.
8. **Bollinger squeeze breakout:** 20-bar band width in the lowest 20% of the last 100 bars on the previous bar, then a
   first close outside the band: trade that way, hold 2 bars.
9. **Fair value gap:** 3-bar gap (bar i low above bar i-2 high, or mirror) at least 0.2 x ATR wide; first later bar
   (within 24) that trades back to the gap edge; enter next open, stop at the far edge of the gap, target 2R, time out 48 bars.

Daily (no random test beyond a day-matched bootstrap):
10. **Fed-day drift:** long NQ from the close before a decision day to that day's close (2011-2020 and 2021-2024).
11. **Power of three:** how often NQ trades below the 00:00 New York price in the first 3 hours, and how often the day
    closes above that price after the dip vs on all days.

## Random opponent (1,000 runs each)
- Time-matched (tests 4-9): each real trade is replaced by an entry at a random bar with the same time of day, same side,
  same exit rule (same stop multiple, or same stop distance for 4 and 9). Compares mean R per trade.
- Coin (tests 1 and 2): same bars, direction replaced by a coin flip.

## Pass rule
A rule passes only if, in BOTH eras and for the same market: mean R after costs > 0; it beats >= 99% of the random runs
(about 14 rule x market trials, so 95% would let one fluke through); both halves of the trades have mean R > 0.
Anything else is rejected. Nothing here changes the Argon book; a pass only earns a proper follow-up batch.
Trials added to the count: 22 (11 rules x 2 markets, fewer where only NQ).

## Not tested (and why)
Volume-based (volume climax, OBV, no-wick volume claims): no volume in our 1-minute files. VWAP bounce: same reason.
Supply/demand, order blocks, CRT, Silver Bullet, kill zones, Judas swing, breaker blocks, double top: no single fixed
mechanical rule in the videos. Dogs of the Dow, Monday effect, all-time highs, Wyckoff spring, Williams breakout on daily
bars, OBV: done earlier on Yahoo daily data (no edge worth trading). Bitcoin, gold and EURUSD rules: no data here.
Psychology, history, crash-day and "how I use AI" videos: no rule.
