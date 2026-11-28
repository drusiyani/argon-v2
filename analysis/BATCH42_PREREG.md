# Batch 42 (28 Nov 2026): trend sleeve - gold (GC) + 10-year Treasury (ZN), monthly momentum

Written and pushed before any run. Source: issue #2 (https://github.com/drusiyani/argon-v2/issues/2), opened by Dru.
One idea = one trial. No parameter sweep.

## Data (fixed)
- `data/extra/GC_daily.csv.gz`, `data/extra/ZN_daily.csv.gz`: Databento ohlcv-1d, continuous front month by volume,
  7 Jun 2010 - 30 Oct 2026. Read directly from `data/extra/` in both eras (same files).
- Bars are dated by `ts_event` (UTC day). A bar dated on a Sunday is merged into the next weekday (its open/high/low
  join that day; the weekday's close is the close). If a Saturday bar exists it is merged the same way.
- Prices are not back-adjusted. On any day the `instrument_id` differs from the previous day's (a roll), that day's
  return = 0, and 1 tick of roll cost is charged on the position held.
- Daily return = close / previous close - 1 otherwise.

## Rules (fixed)
- At each month's last trading day's close (last GC/ZN bar of the calendar month): signal = sign of the market's
  12-month return, compounded from its daily (roll-adjusted) returns from the last close of the same month a year
  earlier. Long if > 0, short if < 0, flat if exactly 0 or not enough history.
- Size: weight = 0.05 / (60-day realised vol x sqrt(252)), from the 60 daily returns up to that close. Weight is a
  fraction of the account (notional / equity). Fractional exposure. Hold until the next month end.
- First signal: end of Jun 2011 (needs 12 months of history), first holding day in Jul 2011.
- Costs: 1 tick each way per unit of notional traded at each rebalance (|new weight - old weight| x tick / price),
  plus 1 tick x |weight| on each roll day. Ticks: GC 0.10, ZN 1/64 point.
- Sleeve daily return on Nasdaq session d = sum of the two markets' weighted returns (after costs) for every GC/ZN day
  after the previous Nasdaq session and up to and including d. (GC/ZN daily closes are about 4 hours after the Nasdaq
  close; this small timing gap is accepted.)

## The book it is compared with (FULL book, because this is a new sleeve)
- Same book as batch 40: Nasdaq core (long close to close, size = min(1.5, 1-year median VXN / VXN), roll days open to
  close) + the four rules at 0.5% (`analysis/batch38.py rules_daily()`, cost cap 0.1R). The pre-FOMC leg and T-bill
  interest are left out of BOTH sides, as in batch 40. Days from the 261st Nasdaq session of each era, as in batch 40.

## Pass bar (fixed)
- Sharpe of book + sleeve must beat the book alone, after costs, in BOTH eras: lockbox2010 (2011-2020) and databento
  (2021/22-2026). Both runs with `ARGON_FULL=1`.

## Also reported (not part of the bar)
- Sleeve's own Sharpe, each market's own Sharpe, correlation with the core, the sleeve's 2022 return, trades
  (rebalances), worst drop of book with/without.
- Luck check (NIGHTLY.md): paired block bootstrap of the Sharpe gain, 21-day blocks, 2000 draws, seed 42, both eras;
  share of draws with gain <= 0. A PASS with era-2 share above 0.10 is labelled "PASS (weak, could be luck)".
- For information only: a whole-contract version on a $100k account (MGC 10 oz, tick $1; ZN $1000/point, tick
  $15.625), nearest whole contracts, no compounding; and the same test with a 2-tick roll cost.
- Trial count: about 331 (330 before tonight + this one).

## Not allowed after seeing results
Changing the 12-month lookback, the 5% vol target, the 60-day vol window, the markets, the monthly rebalance, the
cost rules, the book definition or the pass bar. A failed run may only have its code fixed (bugs, not rules), and each
rerun is noted in the results file.
