# Batch 27 results (15 Nov 2026): recalibrating G3 FAILS. It cut big winners in 2021–26

Pre-registration: `BATCH27_PREREG.md` (committed before the run). Code: `batch27.py`. Raw: `batch27.json`.

| | 2021–26 | 2010–20 | Strict vs G3 | Random beating (of 5,000) |
|---|---|---|---|---|
| G3 | +60.2% / 3.41 / −18.4% / 0.7% | +29.1% / 2.36 / −21.2% / 0.9% | — | — |
| G3c recalibrated | +51.1% / 3.00 / −18.7% / 0.7% | +28.9% / 2.33 / −21.2% / 0.9% | no | 0 |

Sub-periods (return a year / worst drop), G3 → G3c: 2010–13 +17.9% → +18.1%; 2014–17 +14.2% → +13.4%; 2018–20 +68.8% →
+69.1%; **2021–25 +66.1% → +54.6%**; 2026 +30.5% → +32.4%.

## Why
Claude's stated expectation ("roughly the same return") was wrong for 2021–26. When the offset went negative, G3c skipped
extra trades that turned out to be among the best: 2021, 49 trades averaging +0.34R; 2023, 35 trades averaging +0.70R;
2024, 3 trades averaging **+10.8R**. These are tight-stop trades whose predicted edge sat just above the friction line. Most
lose a little, but a few become huge winners in R terms. Lowering the predictions pushed them under the line.
In 2026 it did what was intended (3 extra skips averaging −0.82R, +1.9 points), but that is far too small to pay for 2021–25.

## Lesson
G3's friction hurdle should not be made stricter. The overconfidence found in batch 26 is real, but trading on it removes
the rare large winners that the rules depend on. Protection against a fading edge belongs in a separate stop rule, not in G3.
About 261 trials in total.
