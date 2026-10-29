---
type: changelog
---
# Changelog

## v1.0: frozen, stress-tested (20 Oct 2026)

- **Rules frozen** for the forward test and the AI experiment. See the pre-registration.
- **Stress test** after a harsh outside review: limit orders now need price to trade a full tick through; stops slip (3 ticks in the first 15 minutes); real per-market costs on every trade; no trading on contract roll days; no new trades 8:25–8:40; flat before 2pm on Fed days.
- **Result: the main strategy's edge disappeared** (from +40.8R to −16.3R) and it failed the 2021–23 exam it had passed. The opening range on the Nasdaq held up (Sharpe 0.68 vs 0.02 for random entries), but the portfolio's Sharpe fell to 0.52 and buy-and-hold Nasdaq did better.
- **Deflated Sharpe:** after allowing for ~33,000 versions tried, the chance the portfolio's edge is real is about 0.3%. Most of the earlier edge was generous fills plus the luck of many tries.
- Added data checks (the 9:30 open must line up), confidence ranges, Sortino, buy-and-hold and random-entry benchmarks, and whole micro contracts.

## v0.10

- **The portfolio is now the main strategy plus the opening range on the Nasdaq**, 0.5% risk each. On 5 years of real futures: Sharpe 0.98 (better than either alone, because they barely move together), about +20% a year, worst drop about −40%.
- **The S&P opening range was dropped.** Sharpe 0.33; adding it lowered the portfolio's Sharpe from 0.98 to 0.84.
- **Volatility-scaled sizing was tested and rejected.** Risking less after wild months lowered the Sharpe (0.98 to 0.92) and made the worst drop deeper.
- Cleaned up the design: no gradient text, no glow, no animated borders, no fade-ins, no cursor glow, no badges above headings.

## v0.9

- Tested on 5 years of real CME futures (Databento, 2021–2026, all four markets). The main strategy passed the exam set in advance on 2021–2023.
- **Main strategy now trades the London session only.** New York lost money over the 5 years; London-only was positive in both 2021–23 and 2024–26. Chosen after looking at that data, so the forward test has to confirm it.
- **Opening range can now use a 20-day trend filter** (only trade the way the market's been going). The monthly re-pick currently chooses it for both markets.
- **The order-block strategy was dropped.** It lost money overall on real futures, with a worst drop of about −70R.

## v0.8

- Added a third strategy from published research: the opening-range breakout (Zarattini & Aziz, SSRN 4416622), with real futures trading costs and settings re-picked monthly. Nasdaq and S&P only for now.
- Tested ICT's Silver Bullet hours and Judas swing on the sweep strategy. Neither went in.

## v0.7 · 2026-10-28

- **Fixed a clock bug** in the long backtest: the free history is New York time with daylight saving, and it had been read as fixed winter time, shifting every session by an hour for most of each year. All long-test results before this are wrong.
- With the fix, the main strategy adjusting monthly made -16.31R on 63 unseen months. Not yet proven: see [[Lessons]].
- Now trading the same four markets as Kronos indices.

## v0.4 · 2026-10-28

- Tested on 1487 days of prices (2021-01-04 to 2026-10-01) instead of 50.
- New way of adjusting: every month, re-pick the settings that did best over the previous 6 months. Over 63 test months this beat fixed rules for both strategies, but neither made a reliable profit. See [[Lessons]].
- New settings Claude can use: "same direction as yesterday", "New York first 90 minutes only", "gold only".
- Every trade is now played out on 1-minute candles, so the order of stop and target hits is exact. A new setting, "move the stop to entry at +1R", was tested and not picked.
- This month's rules are in [[Rulebook v1.0]].

## v0.3 · 13 October 2026

- The rules became settings that Claude can adjust. This week's [[Strategy lab — 13 Oct 2026|lab]] tried 1,305 versions; 10 passed the first test; the 5 best all failed on unseen days. **Nothing changed.**
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

