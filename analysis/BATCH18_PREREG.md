# Batch 18 pre-registration (14 Nov 2026) — written and committed BEFORE any batch 18 code was run

Analysis only (does not touch the race). Two tests Dru asked for after the 2026 whipsaw diagnosis and the dealer-gamma
research (14 Nov). About 220 trials so far; this adds 3.

Mark for all three: the STRICT mark against the fixed package (better return and Sortino in both eras, worst drop no more
than 1 point deeper, bootstrap crash chance no more than 1 point higher; 1,000 draws, 63-day blocks, seed 20261111).
The growth mark is reported too, but adoption needs the strict mark.

## Q — QuantLab second chance (targets 2026's "right direction, shaken out first")
Lineage: QuantLab picked the day's direction right 65% of the time in 2026 but most losses were stop-outs before 9:45
(found 14 Nov while explaining 2026). Round 1 tested wider stops, later entry and breakeven stops (all failed), but never a
re-entry.
Rule, for every QuantLab variant: if that variant's trade exits on its stop before 9:45, then at the close of the 9:55–10:00
5-minute bar, if the close is still on the original side of the 12 EMA, enter once more in the original direction at the
10:00 open + 2 ticks. Stop = entry ∓ 0.10 × daily ATR (the ATR stop) for every variant; exit = that variant's own exit rule
(EMA close-back or chandelier 2×/3×), stop slippage 1 tick, flat 15:55 (FOMC days are already skipped). Costs as usual.
The re-entry trades join QuantLab's trade list, so the monthly re-pick sees them like any other trade. Cost cap as usual.
Reported alone: re-entry trades' count and average R in 2010–17, 2018–20, 2021–25 and 2026.

## G — Dealer-gamma regime (SqueezeMetrics GEX)
Data: SqueezeMetrics' free daily GEX estimate for the S&P 500 (squeezemetrics.com/monitor/static/DIX.csv), 2 May 2011 to
13 Nov 2026, downloaded 14 Nov 2026. Kept out of git (analysis/_cache/). It is an S&P measure, used as a market-wide proxy;
there is no free Nasdaq version.
Signal for day d: the latest GEX dated strictly before d, ranked against the previous 252 GEX values (needs 126).
"Low gamma" = below the median (dealers less long gamma, trend-friendly), "high gamma" = at or above.
Days before the data starts: ×1.
- **G1 low-gamma only:** QuantLab / noise band / ATR band trades taken only on low-gamma days (removes trades).
- **G2 gamma reallocation:** ×1.5 on low-gamma days, ×0.5 on high-gamma days.
Lineage: from published research and practitioner commentary, not from scanning Argon's trades. The earlier free proxies
(VIX/VIX3M term structure, VXN regime, VRP) failed, which is a warning.
Diagnostic, reported whatever it shows: the rules' average R per day in low- vs high-gamma days in 2011–17, 2018–20, 2021–26.

## If more than one passes
Report all; no stacking in this batch.

## Not allowed after seeing results
No changing 9:45, 10:00, the stop, the median split, the 252/126 window, the multipliers or the mark.
