# Batch 21 pre-registration (14 Nov 2026) — written and committed BEFORE any batch 21 code was run

Analysis only (does not touch the race). One new idea, from batch 20's correction check. About 230 trials so far.

## Where it came from (not blind)
Batch 20 showed that in 2018 and 2026 QuantLab's direction kept paying after its tight stop was hit (held to the close with
no stop: +1.40R and +1.41R a trade in the trade's own R, against +0.07R and +0.08R actually made), while in 2021 and 2023
the stop saved money. A stopped trade and a held-to-close trade therefore win in different kinds of year. Claude has seen
those by-year figures for the cost-capped book trades. Claude has NOT seen the result on all signal days in 2010–17, where
the cost rule removed 80–97% of QuantLab's trades, or any result in notional terms.

## H — "QuantLab hold" leg
On every QuantLab signal day (the 9:30–9:35 candle closes above/below its 12 EMA; FOMC, roll and bad-data days skipped, as
QuantLab does): enter the Nasdaq future in the signal's direction at the 9:35 open ± 2 ticks, NO stop, exit at the close of
the 15:54 bar ∓ 1 tick. Cost 0.75 points. Size in the package: 0.5× of equity (notional), the same convention as batch 15.
Because there is no tight stop, cost per unit of risk is tiny, so the cost rule does not apply and every signal day counts.

## Marks (fixed now)
1. Alone at 1× notional: positive return and Sharpe ≥ 0.3 in BOTH eras (the edges.py mark).
2. Only if (1) passes: package + leg must meet the STRICT mark against today's package (it adds exposure, so "no extra
   risk" is the right test). The growth mark is reported too.
3. Also reported: skip-only + leg against skip-only, same strict comparison.

## Replication (reported whatever it shows)
The same leg on the S&P future, from the S&P's own QuantLab signals. Replicates if its average daily return is positive in
all three periods (2010–17, 2018–20, 2021–26). Batch 20's search-luck lesson applies: a narrow pass means little.

## Diagnostics
- The leg's average return per day and t-statistic in 2010–17, 2018–20, 2021–25, 2026; its correlation with the rules'
  daily result; what it made on days the stopped QuantLab trade lost.
- QuantLab's picked trades per year BEFORE the cost rule: count, share removed by the rule, gross and net R (to size the
  batch 20 finding).

## Not allowed after seeing results
No changing the entry or exit times, the 0.5×, the marks, or adding filters to the leg.
