# Batch 28 pre-registration (15 Nov 2026) — written and committed BEFORE any batch 28 code was run

Analysis only (does not touch the race). Choosing the stop rule for G3 (Gemini T12 Part 1). About 261 trials so far; adds 3.

## Candidates (each sets the weight of G3's kept trades: 1 / 0.5 / 0)
- **K2** exactly as run in batch 26.
- **K2g** Gemini's T12 version, on the same daily series (G3-kept trades' R at 1×, 0 on days with none; evaluated after each
  day for the next): 1 if PSR₂₅₂ ≥ 0.80 or (coming back from 0.5 or 0) PSR₁₂₆ ≥ 0.85; 0.5 if 0.50 ≤ PSR₂₅₂ < 0.80 and
  PSR₁₂₆ < 0.85; 0 if PSR₂₅₂ < 0.50 and PSR₁₂₆ < 0.85. Needs 252 days, else 1.
- **B** the risk manager's drawdown rule (14 Nov council). Rules to 0.5 when the package falls 15% below its peak; off when
  it falls 22%, or when the rules' shadow R (at 1×) is more than 30R below its own peak. No switching back on within a race.
  For a 16-year backtest a "race" is taken as a calendar year: weight resets to 1 and both peaks reset on 1 January (flagged).

## How one is chosen (fixed now)
None is expected to pass the strict mark against G3 (they are insurance). Report the strict mark anyway. Then pick the
candidate with the HIGHER Sortino in its WORSE era (the minimum of its two eras' Sortino); tie within 0.02 → the one that
costs less return in 2021–25. If no candidate has a higher worse-era Sortino than G3 itself, report that the switch only
costs money on this history, and leave the choice to Dru.

## Also reported
Sub-periods (2010–13, 2014–17, 2018–20, 2021–25, 2026), share of days at each weight, weight on 13 Nov 2026, how many
times each rule cut weight on the core's worst 5% of days (Gemini's "turns off the crisis diversifier" claim), and the
actual daily standard deviation of G3's rules R (Gemini assumed 1.10R for its power estimate).

## Not allowed after seeing results
No changing thresholds, the yearly reset or the selection rule.
