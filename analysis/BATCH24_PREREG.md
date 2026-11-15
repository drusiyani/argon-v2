# Batch 24 pre-registration (15 Nov 2026) — written and committed BEFORE any batch 24 code was run

Analysis only (does not touch the race). Gemini's T9 report ("find skill, not size"), five skip-only proposals.
About 245 trials so far; this adds 5. Source checks before running: the PDT-rule repeal (FINRA Notice 26-10, effective
4 June 2026) is confirmed. Claude could NOT open the two arXiv papers (2605.04004, 2605.11423) to confirm the quoted
statistics (T = −11.52; 77.6%); the tests below do not depend on them.

## The five, exactly as coded
Data: Argon's own 1-minute Nasdaq futures bars with volume (09:30–15:59), daily VXN. 5-minute bars are built on the 09:30 grid.
- **G1 expansion-bar skip.** QuantLab: skip if the 09:30–09:35 range > 1.5 × the mean of the previous 20 days' 09:30–09:35
  ranges (needs 20). Noise band / ATR band: the trigger bar is the 5 minutes ending at the trigger minute (the minute before
  entry); skip if its range > 1.5 × the mean range of the previous 20 RTH 5-minute bars on the 09:30 grid.
- **G2 VVG triple skip.** F1 = |09:30 open − previous 16:00 close| / previous close; F2 = 09:30–09:35 volume / mean of the
  previous 20 days' 09:30–09:35 volume; F3 = |price − 09:30 open| / open, with price = the 09:35 close for entries before 10:00
  and the 10:00 close for entries at or after 10:00. Each compared with the 66.7th percentile of its own earlier values
  (expanding, needs 60 days). If all three are above → skip momentum trades in the direction of the opening move
  (the sign of the same F3 move). Otherwise keep.
- **G3 meta-labelling with a friction hurdle (replaces skip-only, not a filter on top).** The same 24 features and monthly
  walk-forward as W1m, but the ridge is trained on each trade's FRICTION-FREE R (no slippage, no commission; batch 22's method).
  Skip if (A) the prediction is in the bottom third of the previous 252 predictions (needs 100) OR (B) prediction −
  1.25 / stop distance in points ≤ 0 (1.25 = 0.75 commission + 2 ticks, Gemini's figure). Otherwise keep.
- **G4 GTBR dead-zone skip.** Noise band / ATR band only. GTBR = (previous day's VXN close / 100) / √252 (Gemini specified the
  09:30 VXN; Argon only has closes, so the latest known value is used: flagged adaptation). Move = |trigger-minute close −
  09:30 open| / open. Skip if Move / GTBR < 0.50 AND previous VXN close > the Nasdaq's 20-day realised volatility
  (√252 × st.dev. of the last 20 close-to-close returns × 100). Otherwise keep.
- **G5 wick skip.** QuantLab only, the 09:30–09:35 bar: long trades skip if (High − Close) / (High − Low) > 0.50; short
  trades skip if (Close − Low) / (High − Low) > 0.50.

## Marks
- **G1, G2, G4, G5 (filters):** (1) applied alone to today's fixed package, the STRICT mark in both eras; (2) luck test:
  5,000 random rules that skip the same number of the same rule's trades in each year; the filter passes if fewer than 5% of
  them beat its return in BOTH eras; (3) applied on top of skip-only, better return AND Sortino than skip-only in both eras
  with a worst drop no more than 1 point deeper. Adopt-candidate only if all three pass.
- **G3 (a replacement for skip-only):** the STRICT mark against skip-only in both eras, AND fewer than 5% of 5,000 random rules
  (G3's skips shuffled among each year's trades) beat its return in both eras.
- Diagnostics reported whatever they show: skips per year; average R of skipped vs kept trades in 2010–13, 2014–17,
  2018–20, 2021–25, 2026; for G3, the top-minus-bottom ranking gap of its gross prediction in 2012–13 vs W1m's.

## Not allowed after seeing results
No changing any threshold, window, the 1.25, the marks, or combining filters in this batch.
