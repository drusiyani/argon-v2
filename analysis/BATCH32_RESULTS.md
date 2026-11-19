# Batch 32 results: faster-moving skip line FAILS and does not touch July 2026

| | 2021–26 | 2010–20 | July 2026 (at 0.625%) |
|---|---|---|---|
| G3 | +60.2% / 3.41 / −18.4% / 0.7% | +29.1% / 2.36 / −21.2% / 0.9% | −17.5% |
| Q1 (last 63 predictions) | +59.9% / 3.41 / −19.3% / 0.7% | +29.0% / 2.36 / −21.2% / 0.9% | −17.5% |

- Fails the strict mark, the noise floor and the sub-period check (3 of 5).
- Changed 3.5% of calls, **none of them in high-keep months** (including July 2026). Every change was in ordinary
  months, and the trades it newly kept lost 4.7R. So it did the opposite of what was intended.
- Lesson: July's high keep rate was not a drifting skip line. G3 ranked July's trades as genuinely good relative to
  recent weeks too, so no ranking-based tweak can see it. Overconfidence there is a forecasting miss, not a threshold bug.
About 297 trials. No change to the book.
