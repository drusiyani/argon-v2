# Batch 28 results (15 Nov 2026): every stop rule costs money on this history

Pre-registration: `BATCH28_PREREG.md` (committed before the run). Code: `batch28.py`. Raw: `batch28.json`.
Each cell: return a year / Sortino / worst drop / bootstrap chance of a drop worse than −35%.

| | 2021–26 | 2010–20 | Sortino in worse era |
|---|---|---|---|
| G3, no switch | +60.2% / 3.41 / −18.4% / 0.7% | +29.1% / 2.36 / −21.2% / 0.9% | 2.36 |
| K2 rolling PSR (batch 26) | +54.8% / 3.21 / −17.7% / 0.6% | +27.8% / 2.29 / −21.2% / 1.4% | 2.29 |
| K2g (Gemini's T12 version) | +54.3% / 3.18 / −18.4% / 0.6% | +27.6% / 2.28 / −21.2% / 1.4% | 2.28 |
| B drawdown rule | +49.8% / 2.98 / −18.4% / 1.1% | +28.4% / 2.32 / −21.2% / 0.9% | 2.32 |

**By the pre-registered rule:** B has the highest worse-era Sortino of the three candidates, but none beats G3 with no
switch (2.36). So the result is: on this history a stop rule only costs money, and the choice is Dru's.

Sub-periods (return a year), no switch / K2 / B: 2010–13 +17.9 / +18.9 / +17.9; 2014–17 +14.2 / +11.3 / +14.2;
2018–20 +68.8 / +67.0 / +65.7; 2021–25 +66.1 / +62.2 / +55.4; 2026 +30.5 / +19.4 / +22.1.

## Findings
- **Gemini's main objection to B is confirmed.** In 2021–26, B cut the rules on 31 of the core's worst 5% of days and gave up
  58.8R there, because package drawdowns come from Nasdaq sell-offs, which are the rules' best days. K2 gave up 25.9R.
  B costs about 10 points a year in 2021–25.
- **K2 is misfiring now.** It has been at half weight for 63% of 2026, while G3's kept trades made money (+30.5% for the
  package without the switch, +19.4% with it). It reacts to the rules' unfiltered slump, not to G3's own trades going bad.
- **K2g is K2 in practice**: the same weights in every period to within a few days.
- **Gemini's power estimate used too small a spread.** G3's daily rules R has a standard deviation of 2.03R, not the 1.10R it
  assumed. The correlation the AI desk needs to show (about 0.12 for p < 0.05) does not change, but the profit that
  correlation corresponds to is about twice as large in R.

About 264 trials in total.
