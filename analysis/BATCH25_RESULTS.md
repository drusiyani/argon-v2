# Batch 25 results (15 Nov 2026): Gemini T10. All five fail against G3

Pre-registration: `BATCH25_PREREG.md` (committed before the run). Code: `batch25_dump.py`, `batch25.py`. Raw: `batch25.json`.
Each cell: return a year / Sortino / worst drop / bootstrap chance of a drop worse than −35%.

| | 2021–26 | 2010–20 | Strict vs G3 | Random beating (of 5,000) | Skips (2021–26 / 2010–20) |
|---|---|---|---|---|---|
| G3 (reference) | +60.2% / 3.41 / −18.4% / 0.7% | +29.1% / 2.36 / −21.2% / 0.9% | — | — | 34% / 50% |
| T1 stop inside noise | +39.2% / 2.62 / −16.9% / 0.5% | +23.3% / 2.00 / −21.2% / 2.2% | no | 2,754 | 66% / 64% |
| T2 remaining range | +55.4% / 3.18 / −19.0% / 0.7% | +27.8% / 2.28 / −21.5% / 2.2% | no | 895 | 41% / 60% |
| T3 dynamic friction | +60.8% / 3.44 / −18.4% / 0.7% | +27.7% / 2.28 / −21.2% / 1.2% | no (worse in 2010–20) | 0 | 35% / 55% |
| T4 two-stage model | +53.4% / 3.14 / −19.4% / 0.6% | +27.2% / 2.23 / −21.2% / 2.2% | no | 0 | 51% / 68% |
| T5 path efficiency | +50.8% / 3.05 / −20.0% / 1.0% | +28.4% / 2.36 / −21.2% / 0.5% | no | 285 | 50% / 62% |

## What was learned
- **T1's idea is backwards for Argon.** Trades whose stop sat inside the usual 5-minute noise were GOOD trades once G3 had
  already removed those too small to cover costs: +0.23R a trade in 2018–20 and 2021–25 against +0.15–0.16R for the rest.
  Tight stops lose a lot of trades, but the winners are large in R terms. Once friction is covered, a tight stop is not a
  problem in itself.
- **T3 came closest.** Its luck test passed (0 of 5,000) and it edged G3 in 2021–26 (+60.8% vs +60.2%), but it was worse in
  2010–20 (+27.7% vs +29.1%). The extra trades it skipped in 2010–20 had averaged +0.12R (2010–13), +0.09R (2014–17) and
  +0.30R (2018–20): its spread estimate over-penalises the early years.
- **T4 (two-stage) skipped too much** (51% and 68% of trades) and removed trades worth +0.10R to +0.14R a trade in 2018–26.
- **T2 and T5** removed trades that were mostly as good as, or better than, the ones kept.
- Pattern across T9 and T10: G3's simple rule (skip the bottom third and anything whose costs eat the predicted edge) has
  not been improved by any extra skip. Each added rule removed winners along with losers.

No bugs were found. About 255 trials in total.
