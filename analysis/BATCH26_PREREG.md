# Batch 26 pre-registration (15 Nov 2026) — written and committed BEFORE any batch 26 test was run

Analysis only (does not touch the race). Gemini's T11 report. About 255 trials so far; this adds 5.

## What is tested, and what is not
- **Testable from here:** Part 1 Source 1 (mega-cap earnings, SEC EDGAR) and Source 2 (10:00 releases, ALFRED release dates);
  Part 2 kill switches 1–3 (Argon's own trades).
- **Not tested:** Source 3 (Treasury auction API blocked from this workspace), Source 4 (ETF price source blocked),
  Source 5 (daily Wikipedia counts only from July 2015; Gemini's own rule required history to 2012).
- Data fetched 15 Nov 2026 and kept out of git: ALFRED release dates for CPI (10), Employment Situation (50), PPI (46),
  Advance Retail Sales (9), GDP (53), JOLTS (192); SEC 8-K filings and dei:EntityPublicFloat for a fixed list of 22 large
  Nasdaq-100 companies. Universe (chosen now, flagged): AAPL, MSFT, AMZN, GOOGL (incl. Google Inc. before 2015), META, NVDA,
  TSLA, AVGO (incl. Avago), INTC, CSCO, QCOM, CMCSA, AMGN, GILD, NFLX, PEP, COST, ADBE, PYPL, BKNG, TXN, AMD.

## Reference: G3 (batch 24), unchanged. "G3 rank" = the trade's prediction as a percentile of the previous 252 predictions.

## S1 mega-cap pre-earnings freeze (skip on top of G3)
- Top 8 for a year = the 8 universe companies with the largest public float in the latest 10-K filed before 1 January of
  that year (Gemini asked for trailing dollar volume; no price data here, so public float from SEC is used: flagged).
- MegaReaction(d): a top-8 company's 8-K with item 2.02 accepted between 16:00 ET on the previous trading day and 09:30 ET on d.
- Tier-1 day: a CPI, Employment Situation, PPI, Advance Retail Sales, GDP or JOLTS release date, or an ISM date (first and
  third business day of the month, by rule: flagged, ISM is not on ALFRED).
- PreMegaFreeze(d): no MegaReaction, not a Tier-1 day, and at least two top-8 companies file an item-2.02 8-K after 16:00 ET
  on d or on the next trading day (actual filing times stand in for the published schedule: flagged).
- Action: on PreMegaFreeze days, also skip G3-kept trades with a G3 rank below 66.7% (keep only G3's top third).

## S2 10:00 release collision (skip on top of G3)
- 10:00 day: a JOLTS date or an ISM date (rule as above). University of Michigan dates are excluded: ALFRED's dates for that
  release lag the real release (flagged).
- Action: on 10:00 days that are NOT CPI / Employment Situation / PPI / Advance Retail Sales / GDP dates, skip QuantLab
  trades whose G3 net edge (prediction − 1.25 / stop) is below the median net edge of the previous 252 G3-judged trades.

## K1 CUSUM, K2 rolling PSR, K3 Bayesian changepoint (rules weight 1 / 0.5 / 0 on top of G3)
All three watch G3-kept trades (paper-tracked even when the switch is off) and set the weight of the next trades.
- **K1:** μ₀, σ₀ = mean and standard deviation of R after costs of all G3-kept trades before the current calendar year
  (needs 200; before that the weight is 1). z = (R − μ₀) / σ₀; C = max(0, C − z − 0.25), capped at 8.03.
  Weight: 1 → 0.5 when C ≥ 4.0; → 0 when C ≥ 8.03. From 0, back to 0.5 when C < 4.015; back to 1 when C = 0.
- **K2:** daily R of G3-kept trades (0 on days with no trade). At each day's end, over the last 252 days: Sharpe (per day),
  skewness γ₃, kurtosis γ₄; PSR = Φ(SR·√(T−1) / √(1 − γ₃·SR + (γ₄ − 1)/4·SR²)). Weight for the next day: 1 if PSR ≥ 0.80,
  0.5 if 0.50 ≤ PSR < 0.80, 0 if PSR < 0.50; from 0, back to 0.5 when PSR₂₅₂ ≥ 0.50 or PSR over the last 126 days ≥ 0.85.
  Needs 252 days, else 1.
- **K3:** Adams & MacKay run-length recursion on G3-kept trades' R, hazard 1/150, Normal-Inverse-Gamma prior
  (μ 0, κ 1, α 1, β 1). P(μ > 0) = the run-length-weighted Student-t probability. Weight: 1 → 0.5 when P < 0.75; → 0 when
  P < 0.50; from 0 or 0.5, back to 0.5 when P ≥ 0.65 and to 1 when P ≥ 0.80. Gemini's half-life condition is NOT
  implemented: its formula was missing from the report (flagged).

## Marks
- S1, S2: STRICT mark against G3 in both eras, AND fewer than 5% of 5,000 random rules (the same number of extra skips per
  year, placed at random among G3-kept trades) beat its return in both eras.
- K1–K3: adopt-candidate only on the STRICT mark against G3 in both eras. Whatever happens, reported for Dru to decide:
  return and worst drop in 2010–13, 2014–17, 2018–20, 2021–25 and 2026; share of days at each weight; and the weight each
  would hold on 13 Nov 2026.

## Diagnostics (Gemini's red-team, Part 4)
- Risk 2: by year, G3's average prediction vs the average friction-free R of the trades it kept.
- Risk 5: confirm from the code whether "yesterday's rules result" uses all of yesterday's trades or only those G3 kept.

## Not allowed after seeing results
No changing the universe, thresholds, windows, hazard, prior or marks.
