---
type: changelog
---
# Changelog

## v0.8

- Added a third strategy from published research: the opening-range breakout (Zarattini & Aziz, SSRN 4416622), with real futures trading costs and settings re-picked monthly. Nasdaq and S&P only for now.
- Tested ICT's Silver Bullet hours and Judas swing on the sweep strategy. Neither went in.

## v0.7 · 2026-10-15

- **Fixed a clock bug** in the long backtest: the free history is New York time with daylight saving, and it had been read as fixed winter time, shifting every session by an hour for most of each year. All long-test results before this are wrong.
- With the fix, the main strategy adjusting monthly made +16.75R on 27 unseen months. Not yet proven: see [[Lessons]].
- Now trading the same four markets as Kronos indices.

## v0.4 · 2026-10-15

- Tested on 711 days of prices (2024-01-02 to 2026-10-01) instead of 50.
- New way of adjusting: every month, re-pick the settings that did best over the previous 6 months. Over 27 test months this beat fixed rules for both strategies, but neither made a reliable profit. See [[Lessons]].
- New settings Claude can use: "same direction as yesterday", "New York first 90 minutes only", "gold only".
- Every trade is now played out on 1-minute candles, so the order of stop and target hits is exact. A new setting, "move the stop to entry at +1R", was tested and not picked.
- This month's rules are in [[Rulebook v0.8]].

## v0.3 · 13 October 2026

- The rules became settings that Claude can adjust. This week's [[Strategy lab — 13 Oct 2026|lab]] tried 1,305 versions; 12 passed the first test; the 5 best all failed on unseen days. **Nothing changed.**
- Added Argon v1's risk rules.
- Added a "day's direction" check, and a bad luck / bad reasoning verdict on losing trades.
- See [[Lessons]].

## v0.2

- [[The main strategy]] with a full list of checks, plus [[The order-block strategy]] as a second strategy.
- Skipped trades are now played out in the background ([[Skipped trades]]).
- **Fixed a [[No peeking at the future|peeking-at-the-future]] mistake.** Before the fix the order-block strategy showed +20.7R; after, it lost money.

## v0.1

- First version, on 5-minute candles. 10 trades, −4.39R.

%% my notes below. Argon never changes anything under this line %%
## My notes

