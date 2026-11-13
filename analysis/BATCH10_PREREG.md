# Batch 10 pre-registration (13 Nov 2026) — written and committed BEFORE any batch 10 code was run

Analysis only (does not touch the race). Dru asked for gaps in the ~170 tests so far (Claude's and Gemini's) that could raise
profit WITHOUT raising risk. Review of the record: every test used the Nasdaq's regular-session prices, volatility indices,
the calendar, dealer gamma or the book's own results. Three sources of information have never been used:
real futures volume (the free data only had tick counts), the market's reaction to the 8:30am news releases, and whether
the S&P confirms a Nasdaq move at the moment of entry. Each test below moves size around or removes trades. None adds size.

Baseline = the FIXED package. Pass mark, same as batches 5–9: ADOPT only if, in BOTH eras (2021–26 and 2010–20), vs the fixed
package: higher per-year return AND higher Sortino AND worst drop no more than 1 point deeper AND bootstrap chance of a drop
worse than −35% no more than 1 point higher (1,000 draws, 63-day blocks, seed 20261111). Each idea is tested alone.

## G1 — S&P confirmation at entry (removes trades)
Why: index-wide moves are pushed along by hedging flows (Baltussen et al. 2021), while moves driven by single-company news
tend to reverse within the day (Park & Zhao 2025; Baltussen, Da & Soebhag 2024). A Nasdaq breakout the S&P does not share is
more likely the second kind.
Rule: a QuantLab / noise band / ATR band trade is kept only if, at the last 1-minute close before entry, the S&P future's move
from its own 9:30 open, in units of its own ATR(14), is in the trade's direction and at least half the Nasdaq's move in units
of its ATR(14). The "half" is Claude's choice, not from a paper (flagged). Expiry trades unchanged. If the S&P bar is missing,
the trade is kept.

## G2 — 8:30 news-shock reallocation (moves size, average 1)
Why: Gao et al. (2018) report stronger intraday momentum on days with major economic news. Instead of a calendar, the size of
the Nasdaq future's own reaction is used, which is known an hour before the open.
Rule: shock = |close of 08:34 / close of 08:29 − 1| on the Nasdaq future. Each day it is ranked against the previous 252 days
(need 60): bottom third → all rule trades that day ×0.5, middle ×1, top third ×1.5 (on top of the usual 0.5). Else ×1.

## G3 — Pre-market volume reallocation (moves size, average 1)
Why: Gao et al. (2018) also report stronger intraday momentum on high-volume days, and Zarattini's "in play" work finds
unusual volume marks the days that trend. Real CME volume has never been used in Argon.
Rule: Nasdaq-future volume from 04:00 to 09:29 New York, ranked against the previous 252 days (need 60):
bottom third ×0.5, middle ×1, top third ×1.5. Else ×1.

## Not allowed after seeing results
No changing the half, the windows, the thirds, the multipliers or the pass marks. Nothing is combined unless it passes alone.
