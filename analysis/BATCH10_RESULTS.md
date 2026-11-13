# Batch 10 results (13 Nov 2026): nothing passes

Rules and pass marks: `BATCH10_PREREG.md` (committed before the run). Code: `batch10.py`. Raw: `batch10_*.json`.
Each cell: return a year / Sortino / worst drop / bootstrap chance of a drop worse than −35%.

| | 2021–26 | 2010–20 | Verdict |
|---|---|---|---|
| Package baseline | +56.4% / 3.18 / −19.4% / 1.0% | +21.6% / 1.75 / −23.5% / 7.4% | — |
| G1 S&P confirmation at entry | +42.5% / 2.63 / −21.2% / 1.2% | +21.4% / 1.79 / −23.1% / 5.4% | FAIL |
| G2 8:30 news-shock reallocation | +55.9% / 3.04 / −22.9% / 4.6% | +25.9% / 1.98 / −23.7% / 5.1% | FAIL (passes 2010–20 only) |
| G3 pre-market volume reallocation | +47.4% / 2.63 / −22.6% / 9.8% | +25.8% / 1.90 / −26.1% / 13.4% | FAIL |

- **G1:** the hypothesis was backwards. In 2021–26 the trades the S&P did NOT confirm were the better ones (+0.14R a trade
  against +0.09R for confirmed ones). Nasdaq-only moves trended more, not less. In 2010–20 there was no difference.
- **G2:** in 2010–20 the rules lost on quiet-news days (−0.10R a day) and made money on big-reaction days (+0.09R), so moving
  size to those days helped a lot. In 2021–26 the three groups were the same (+0.25 / +0.21 / +0.26R), so it did nothing but
  add lumpiness.
- **G3:** the two eras disagree outright. High pre-market volume days were the best in 2010–20 and the worst in 2021–26.

Same pattern as batches 4–9: a filter that helps one decade does nothing for, or hurts, the other.
Trial count is now about 178.
