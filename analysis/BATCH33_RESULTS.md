# Batch 33 results: both of Gemini's overconfidence fixes FAIL

| | 2021–26 | 2010–20 | Sub-periods level+ | July 2026 at 0.625% |
|---|---|---|---|---|
| G3 | +60.2% / 3.41 / −18.4% / 0.7% | +29.1% / 2.36 / −21.2% / 0.9% | — | −17.5% |
| H1 hinged yesterday R | +58.5% / 3.34 / −17.8% / 0.3% | +28.1% / 2.31 / −21.3% / 2.6% | 1 of 5 | −16.8% |
| H2 variance-ratio feature | +59.0% / 3.36 / −18.2% / 0.5% | +27.7% / 2.26 / −21.2% / 2.2% | 2 of 5 | −16.8% |

- Diagnosis confirmed (attribution): yesterday's rules result drove about half of July's prediction jump.
- But fixing it barely helps July (−17.5% → −16.8%) and costs return in most other periods: losing days are, on
  average across 16 years, genuinely followed by better trades. Removing that signal to save one month is a bad trade.
- H2 note: Gemini's pooled formula divides by 6 × the 5-minute sum, which puts the ratio 6× too low (ln 6 = 1.79 off).
  This is a constant, so after standardisation the test is unaffected (mean ln VR −1.81 + 1.79 ≈ −0.02, a random walk).
About 299 trials. No change to the book. Overconfidence in grinding months is accepted as a cost of the edge.
