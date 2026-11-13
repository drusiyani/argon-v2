# Batch 9 results (13 Nov 2026): nothing passes; one narrow miss (H3)

Rules and pass marks: `BATCH9_PREREG.md` (committed before the run). Code: `batch9.py`, `batch9_ml.py`. Raw: `batch9_*.json`.
Each cell: return a year / Sortino / worst drop / bootstrap chance of a drop worse than −35%.

| | 2021–26 | 2010–20 | Verdict |
|---|---|---|---|
| Package baseline | +56.4% / 3.18 / −19.4% / 1.0% | +21.6% / 1.75 / −23.5% / 7.4% | — |
| H1 regime tilt of the rules | +57.7% / 3.17 / −20.8% / 1.2% | +23.1% / 1.77 / −27.1% / 17.3% | FAIL |
| H2 overnight after a down day | +58.3% / 2.95 / −20.8% / 1.8% | +23.3% / 1.68 / −29.1% / 17.7% | FAIL |
| H3 vol-managed package size | +65.2% / 3.51 / −19.9% / 1.2% | +23.6% / 1.92 / −22.5% / 8.7% | FAIL by 0.3 points |
| H4 European-session noise band | +37.2% / 1.89 / −37.7% / 64.6% | +19.3% / 1.54 / −23.2% / 9.8% | FAIL |
| H5 learned sizing (other era's model) | +62.0% / 3.40 / −22.7% / 1.6% | +24.6% / 1.86 / −27.8% / 16.9% | FAIL |

- **H3** beat the package on return, Sortino and Sharpe in both eras, with a shallower real worst drop in 2010–20. It passed
  2021–26 outright. It failed 2010–20 on one mark only: the bootstrap crash chance rose 1.3 points (7.4% → 8.7%) and the limit
  is 1.0. By the rule that is a FAIL, the same way the Fed-day skip failed by 0.1. Average size was 1.01×, so the gain came
  from timing the size, not from more size.
- **H1, H2, H5** all raised the return in both eras, but each made the drops deeper. That is more risk, not more edge.
  H5's model did carry some real signal across eras (in 2021–26, days it sized up averaged +0.37R against +0.12R for days it
  sized down, using a model that had only seen 2010–20), but not enough to pay for the extra drop.
- **H4** lost money on its own in both eras (−0.07R and −0.04R a trade). Momentum does not survive costs before the US open.

One bug was fixed during the run, before any 2010–20 number was seen: days whose first bar was 03:01–03:05 crashed H4.
The 2021–26 output was identical before and after the fix.

No combination test and no leverage re-test, because nothing passed.
