# Batch 24 results (15 Nov 2026): Gemini T9. One passes everything (G3); four fail

Pre-registration: `BATCH24_PREREG.md` (committed before the run). Code: `batch24_dump.py`, `batch24.py`. Raw: `batch24.json`.
Each cell: return a year / Sortino / worst drop / bootstrap chance of a drop worse than −35%.

| | 2021–26 | 2010–20 |
|---|---|---|
| Package (fixed size) | +56.4% / 3.18 / −19.4% / 1.0% | +21.6% / 1.75 / −23.5% / 7.4% |
| Skip-only (current main book) | +57.9% / 3.30 / −18.8% / 0.8% | +28.5% / 2.29 / −21.2% / 2.4% |
| **G3 meta-labelling + friction hurdle** | **+60.2% / 3.41 / −18.4% / 0.7%** | **+29.1% / 2.36 / −21.2% / 0.9%** |

## G3 — passes every mark
- Strict mark against skip-only: yes, in both eras (better return and Sortino, shallower or equal drop, lower crash chance).
- Luck test: 0 of 5,000 random rules (G3's own skips shuffled among each year's trades) beat its return in both eras.
- It skips more than skip-only: 34% of momentum trades in 2021–26 and 50% in 2010–20. Of 6,060 trades it judged, 1,588 were
  skipped for both reasons, 576 only because the predicted edge did not clear the trade's friction, 401 only for being in the
  bottom third.
- Ranking (top third minus bottom third, R per trade), G3's friction-free model / the current model: 2012–13 +0.17 / +0.14;
  2014–17 +0.10 / +0.11; 2018–20 +0.31 / +0.29; 2021–26 +0.21 / +0.19. Slightly better in three of four periods.
- What the gain is, honestly: most of it is the friction hurdle, i.e. skipping trades whose stop is so tight that costs eat
  the predicted edge. That is knowable at entry and legitimate, but it is closer to "a smarter cost rule" than to "better
  market prediction". The 2010–20 gain is mostly risk (crash chance 2.4% → 0.9%); return rises only 0.6 points.
- Caveats: one pass after about 250 trials (the luck test is the main defence); the 1.25-point friction is Gemini's figure;
  the 24 features carry hindsight from batches 11–12.

## G1, G2, G4, G5 — fail

| | Alone on the package (2021–26 / 2010–20) | Strict | Random rules beating it (of 5,000) | On top of skip-only |
|---|---|---|---|---|
| G1 expansion-bar skip | +53.2% / +23.4% | no | 317 | worse in 2021–26 |
| G2 VVG triple skip | +44.8% / +19.4% | no | 4,512 | worse in both |
| G4 GTBR dead-zone skip | +56.0% / +23.8% | no | 76 | worse in 2021–26 |
| G5 wick skip | +50.5% / +22.7% | no | 460 | worse in 2021–26 |

- **G2 has the sign backwards for Argon.** The trades it skipped were among the best: +0.39R a trade in 2021–25 and +0.38R in
  2026, against +0.10R and +0.01R for the trades it kept. On high-stress opening days, Argon's rules make their money.
- **G5 is interesting but split.** Its skipped trades lost heavily in 2026 (−0.57R a trade, 34 trades) and 2018–20 (−0.13R), but
  made +0.40R in 2021–25. Not stable.
- G1 and G4 skipped trades that were sometimes better, sometimes worse than the rest; no consistent pattern.

Bugs fixed before any result was seen: per-day bar lists were read as dicts (all flags came out zero) and a missing index.
A diagnostic column printed "nan" in the first run and was recomputed afterwards; no mark depends on it.
