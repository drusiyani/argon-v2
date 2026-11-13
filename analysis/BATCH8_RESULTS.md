# Batch 8 results (13 Nov 2026): both rules FAIL, no leverage re-test

The rules and pass marks were set in `BATCH8_PREREG.md` (committed before the run). Code: `batch8.py`. Raw: `batch8_*.json`.

| | 2021–26 return / Sortino / worst drop | 2010–20 return / Sortino / worst drop | Verdict |
|---|---|---|---|
| Package baseline | +56.4% / 3.18 / −19.4% | +21.6% / 1.75 / −23.5% | — |
| + S1 spread reversion | +51.9% / 2.93 / −20.0% | +21.1% / 1.72 / −24.0% | FAIL |
| + S2 calm-day fade | +55.9% / 3.13 / −18.9% | +20.7% / 1.67 / −25.3% | FAIL |

What each rule did on its own:
- **S1 spread:** lost in both eras (−0.05R a trade over 625 trades in 2021–26, and −0.05R over 173 trades in 2010–20). Most trades
  ran to the close without the gap closing. When the Nasdaq pulls away from the S&P during the day, it usually keeps going.
- **S2 calm fade:** it did act as a hedge (it made +13R and +30R on the package's losing days, and its correlation with the
  package was −0.11 to −0.14), but it lost more on other days, so the total was negative in both eras.

**Lesson:** fading the Nasdaq during the day lost money even in calm markets. Add this to the overnight-reversal fail. The book's
edge is intraday momentum, and the opposite side of that trade doesn't pay.

Under the pre-registration, there's no leverage re-test because nothing passed. The 1.25× numbers in the JSON are diagnostics
only: the package at 1.25× still has a 21% (2021–26) and 42% (2010–20) chance of a drop worse than −35%.
