# Batch 45 (28 Nov 2026): currency carry from the futures basis

Written and pushed before any run. Source: issue #4. One idea = one trial. No parameter sweep.

## Why
Carry (long high-interest-rate currencies, short low-rate ones) is one of the oldest known currency premia
(Koijen, Moskowitz, Pedersen & Vrugt, "Carry", JFE 2018). Who is on the other side: hedgers and central banks who pay
to hold low-rate currencies. Known risk: it crashes in panics (2008), so it may correlate with the Nasdaq core.

## Data (fixed)
- Returns: `data/extra/{6E,6J,6B,6A,6C}_daily.csv.gz` (front by volume, `.v.0`).
- Carry signal: `data/extra/{M}_c0_daily.csv.gz` and `{M}_c1_daily.csv.gz` (nearest and next contract by calendar).

## Rules (fixed)
- At each month end, for each currency: basis = ln(next close / nearest close) on that day (both bars present and
  with different `instrument_id`s; else use the latest earlier day that has both, up to 5 days back, else skip that
  currency this month). Carry = -4 x basis (contracts are quarterly; a cheaper next contract means a higher foreign rate).
- Rank the currencies by carry. Long the top 2, short the bottom 2, middle one flat. Need at least 4 currencies with a
  signal, else flat all that month.
- Weight per position = 0.025 / (60-day realised vol x sqrt(252)) from the `.v.0` returns. Hold to the next month end.
- Ticks as batch 44. First signal end of Jun 2010 + 60 days of vol (first full month end with 60 days of history).

## The book it is compared with
- Base = the batch 42 book (Nasdaq core + the four rules at 0.5%, exactly as in `analysis/batch42.py`) PLUS the batch 42
  GC+ZN trend sleeve, because that sleeve is the live candidate for Amendment 14. The idea is added on top of that.
- Also reported (not the bar): the same comparison against the book alone, without the batch 42 sleeve.

## Pass bar (fixed)
- Sharpe of base + idea must beat the base, after costs, in BOTH eras: lockbox2010 (2011-2020) and databento
  (2021/22-2026). Both runs with `ARGON_FULL=1`.
- Luck check as in NIGHTLY.md (paired block bootstrap of the gain vs the base, 21-day blocks, 2000 draws, seed 42).
  A PASS with era-2 share above 0.10 is labelled "PASS (weak, could be luck)".

## Data handling (same as batch 42)
- Daily Databento bars; Sunday/Saturday bars merged into the next weekday; on an `instrument_id` change the day's
  return = 0 and 1 tick of roll cost is charged on the position held. Rebalance cost: 1 tick x |change in weight| / price.
- The idea's daily returns are summed onto Nasdaq sessions exactly as batch 42 does (`on_sessions`).
- Run in GitHub Actions only, one run, both eras. Code bugs may be fixed and rerun; every rerun is noted.

## Also reported
- The carry leg's own Sharpe, correlation with the core, the worst month, 2022 return.
- Trial count: about 334.

## Not allowed after seeing results
Changing the markets, top/bottom 2, the 4x annualising, the 2.5% vol target, the 60-day window, monthly rebalance,
costs, base book or pass bar.
