# Batch 26 results (15 Nov 2026): Gemini T11. Nothing passes; one kill switch is worth considering as insurance

Pre-registration: `BATCH26_PREREG.md` (committed before the run). Code: `batch26.py`. Raw: `batch26.json`.
Data: ALFRED release dates and SEC EDGAR filings, fetched 15 Nov 2026 (in `analysis/_cache/ext26/`, not in git).
Each cell: return a year / Sortino / worst drop / bootstrap chance of a drop worse than −35%.

| | 2021–26 | 2010–20 | Strict vs G3 | Random beating (of 5,000) |
|---|---|---|---|---|
| G3 (reference) | +60.2% / 3.41 / −18.4% / 0.7% | +29.1% / 2.36 / −21.2% / 0.9% | — | — |
| S1 mega-cap pre-earnings freeze | +60.9% / 3.45 / −17.6% / 0.6% | +29.0% / 2.36 / −21.2% / 0.9% | no | 439 (8.8%) |
| S2 10:00 release collision | +55.7% / 3.22 / −21.1% / 1.7% | +28.7% / 2.33 / −21.2% / 1.2% | no | 4,217 |
| K1 CUSUM | +56.4% / 3.24 / −18.4% / 0.9% | +28.7% / 2.38 / −21.2% / 0.8% | no | — |
| K2 rolling PSR | +54.8% / 3.21 / −17.7% / 0.6% | +27.8% / 2.29 / −21.2% / 1.4% | no | — |
| K3 Bayesian changepoint | +34.0% / 2.23 / −20.5% / 3.3% | +25.4% / 2.16 / −21.2% / 0.6% | no | — |

## Part 1 sources
- **S1** fired on only 108 days in 16 years and removed 35 trades. It helped in 2026 (its 7 removed trades averaged −0.70R)
  but was flat everywhere else and failed the luck test (8.8% of random rules did as well). Too rare to judge.
- **S2** removed QuantLab's best trades: those skipped averaged +0.84R (2018–20), +0.73R (2021–25), +2.84R (2026, 5 trades).
  Mornings before a 10:00 release are good for QuantLab, not bad.
- Sources 3–5 were not tested (data blocked here, or history too short).

## Part 2 kill switches, by sub-period (return a year / worst drop)

| | 2010–13 | 2014–17 | 2018–20 | 2021–25 | 2026 | Weight on 13 Nov 2026 |
|---|---|---|---|---|---|---|
| G3, no switch | +17.9% / −21.2% | +14.2% / −19.8% | +68.8% / −18.4% | +66.1% / −17.7% | +30.5% / −18.4% | 1 |
| K1 CUSUM | +17.9% / −21.2% | +14.6% / −18.7% | +66.6% / −18.1% | +63.1% / −17.7% | +23.4% / −18.4% | 1 |
| K2 rolling PSR | +18.9% / −21.2% | +11.3% / −19.4% | +67.0% / −18.4% | +62.2% / −17.7% | +19.4% / −16.1% | **0.5** |
| K3 Bayesian changepoint | +19.5% / −21.2% | +14.6% / −17.0% | +49.2% / −15.2% | +35.4% / −20.5% | +26.7% / −13.2% | 1 |

- **K1** was inactive until 200 trades of history existed, so it never acted in 2010–13. It cost about 2–3 points a year
  in the good years and 7 points in 2026. Gemini's description of what it "would have done" did not match.
- **K2** is the only one that behaved like insurance: it was at half or zero weight for most of 2014–17 (a weak stretch),
  stayed on through 2018–25, and has been at half weight for 63% of 2026. Cost: about 4 points a year in the good years.
  It is at half weight now.
- **K3** is far too jumpy with these settings: it spent 50–66% of the time switched off, in good years and bad.
- None passed the strict mark. Any kill switch is insurance, and insurance has a price.

## Part 4 checks
- **Risk 2 (G3 is overconfident when the edge fades): confirmed.** G3's average prediction for the trades it kept vs what
  they actually made before friction: 2024 +0.23 vs +0.35; 2025 +0.26 vs +0.20; **2026 +0.26 vs +0.12**. Also too high in
  2013 (+0.21 vs −0.05) and 2016 (+0.17 vs +0.04). Its trades still made money in 2026 (+0.10R a trade after costs,
  about +30R), but the friction hurdle is relying on predictions that are about twice too high.
- **Risk 5 (live feature bug): confirmed as a live risk, not a backtest bug.** In the backtest, "yesterday's rules result"
  is computed from ALL of yesterday's rule trades, before any skipping. The live engine must do the same, from shadow
  trades, or the feature will read zero on skipped days.
