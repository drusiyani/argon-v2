# Batch 12 results (13 Nov 2026): two passes (not blind), combination fails by 0.2 points, S&P replication partial

Pre-registration and addendum: `BATCH12_PREREG.md`. Code: `batch12.py`, `batch12_es.py`. Raw: `batch12_*.json`.
Each cell: return a year / Sortino / worst drop / bootstrap chance of a drop worse than −35%.

| | 2021–26 | 2010–20 | Verdict |
|---|---|---|---|
| Package baseline | +56.4% / 3.18 / −19.4% / 1.0% | +21.6% / 1.75 / −23.5% / 7.4% | — |
| M1 day-after reallocation (lost ×1.5, won ×0.5) | +70.3% / 3.58 / −24.2% / 2.2% | +30.1% / 2.26 / −25.0% / 6.6% | FAIL (drops deeper) |
| M2 skip the day after a win above 2R | +60.6% / 3.46 / −19.0% / 0.4% | +26.0% / 2.11 / −23.2% / 5.0% | PASS |
| M3 gap-and-yesterday reallocation | +63.5% / 3.41 / −20.3% / 1.0% | +27.2% / 2.11 / −20.0% / 4.5% | PASS |
| M2 + M3 together | +67.4% / 3.69 / −20.6% / 0.9% | +30.7% / 2.38 / −20.2% / 3.6% | FAIL (2021–26 drop 1.2 pts deeper, limit 1.0) |

These are the first passes in about 185 ideas. They were EXPECTED to pass, because the patterns were found by scanning this
same data (19 attributes). Treat the size of the gains as an upper limit.

**S&P replication (defined before running): partial, 2 of 3 periods each, so the stated bar (3 of 3) was NOT met.**
- Day after a win above 2R vs other days, ES rules, R per day: 2010–17 −0.25 vs −0.06 (same as Nasdaq); 2018–20 +0.04 vs −0.05
  (opposite, 51 days); 2021–26 −0.22 vs −0.03 (same).
- With gap and against yesterday vs the reverse, R per ES trade: 2010–17 +0.02 vs −0.11 (same); 2018–20 −0.05 vs +0.03
  (opposite); 2021–26 +0.06 vs −0.05 (same).

**Leverage (reported only):** at 1.25×, M2 gives +76.9% / −23.6% (13.6% of bootstraps below −35%) in 2021–26 and
+32.4% / −28.4% (30.7%) in 2010–20. The 2010–20 crash chance is still over the 20% limit, so leverage still fails.

M2 skips about 10–13% of momentum trades. M3's average trade size is 1.03–1.04×.
Status: M2 and M3 are candidates for shadow books in Race 1, or for an openly flagged amendment if Dru chooses. Not both
together, because the combination did not pass.
