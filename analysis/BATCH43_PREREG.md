# Batch 43 (28 Nov 2026): month-end stock-bond rebalancing trade on NQ

Written and pushed before any run. Source: Claude's own idea (nightly lab, 28 Nov 2026), proposed with the Gemini
filters in `lab/gemini_idea.py` after the queue gave only one idea. One trial. No parameter sweep.

## Why it might work
Pensions and balanced funds hold fixed stock/bond weights and rebalance on the calendar, mostly at month end. When
stocks have beaten bonds during the month, they must sell stocks and buy bonds near month end (and the reverse). That
flow is forced and known in advance. Harvey, Mazzoleni and Melone, "The Unintended Consequences of Rebalancing"
(NBER w33554, 2025) find stock returns are lower around month end after stocks outperformed bonds, and higher after
they underperformed. Who loses: the rebalancers, who trade on a fixed clock regardless of price.

## Why it is not in TRIED.md
Closest past tests: turn of the month (b40) and pre-holiday (b40), both unconditional LONG trades. This one is long or
short, with the side set by the month's stock-vs-bond race. It is not a long-Nasdaq bet (it is short about half the
time) and not a filter or tilt of the core or the rules.

## Rules (fixed)
- T = the last NQ session of each calendar month. E = the session 5 sessions before T.
- At E's close: rel = ES return from the previous month's last session close to E's close, minus ZN return over the
  same days. ES: regular-session closes (`c.daily('ES')`), roll days open to close (as the core). ZN: daily bars from
  `data/extra/ZN_daily.csv.gz`, Sunday bars merged into the next weekday, roll day return = 0 (as batch 42), all ZN
  days dated after the previous month's last NQ session and up to E's date.
- Trade: NQ, side = -1 if rel > 0 (stocks beat bonds: short), +1 if rel < 0, none if 0 or data missing.
  Size 1x the account (notional / equity = 1), fixed. Hold from E's close to T's close (5 sessions).
- Daily P&L = side x NQ close-to-close return (roll days open to close, |move| > 15% set to 0, as in batch 40).
- Cost: 1.1 NQ points per round trip (as batch 40), charged on the first holding day, divided by E's close.

## Pass bar (fixed)
- Compared on the FULL book, as in batch 40: core (min(1.5, 1-yr median VXN / VXN), close to close) + four rules at
  0.5%. Book + trade must beat book alone in Sharpe, after costs, in BOTH eras: lockbox2010 (2011-2020) and databento
  (2021/22-2026), both under `ARGON_FULL=1`. Days from the 261st Nasdaq session of each era.

## Also reported (not part of the bar)
- Trades, win rate, average return per trade after costs, own Sharpe, correlation with the book, hit rate by side.
- Luck check (NIGHTLY.md): paired block bootstrap of the Sharpe gain, 21-day blocks, 2000 draws, seed 42, both eras;
  share of draws with gain <= 0. PASS with era-2 share above 0.10 = "PASS (weak, could be luck)".
- Trial count: about 332 (after batch 42).

## Not allowed after seeing results
Changing the 5-session window, the signal (ES minus ZN month-to-date), the 1x size, ES as the stock leg, the cost, the
book or the pass bar. Code bugs only may be fixed; every rerun is noted in the results file.
