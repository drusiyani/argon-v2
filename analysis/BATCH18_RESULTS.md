# Batch 18 results (14 Nov 2026): both ideas fail; the gamma result flips between eras

Pre-registration: `BATCH18_PREREG.md` (committed before the run). Code: `batch18.py`. Raw: `batch18_*.json`.
Each cell: return a year / Sortino / worst drop / bootstrap chance of a drop worse than −35%.

| | 2021–26 | 2010–20 | Strict | Growth |
|---|---|---|---|---|
| Package baseline | +56.4% / 3.18 / −19.4% / 1.0% | +21.6% / 1.75 / −23.5% / 7.4% | — | — |
| Q QuantLab second chance | +51.7% / 2.83 / −21.9% / 6.6% | +18.8% / 1.53 / −24.9% / 14.2% | no | no |
| G1 low-gamma days only | +28.5% / 1.90 / −23.0% / 6.5% | +27.0% / 2.17 / −21.8% / 4.5% | no (passes 2010–20 only) | no |
| G2 gamma reallocation | +45.3% / 2.61 / −25.2% / 3.7% | +27.6% / 2.06 / −25.5% / 12.1% | no | no |

## Q — the second chance loses everywhere, worst of all in 2026
Re-entry trades (all six variants, before the monthly re-pick), average R after costs:
2010–17 −0.26 (2,813 trades), 2018–20 −0.21 (982), 2021–25 −0.01 (1,798), **2026 −0.25 (376)**.
When QuantLab is shaken out early, the second attempt usually gets shaken out too. Being "right on the direction" by the
close does not help when the path keeps whipping. Hypothesis rejected.

## G — dealer gamma: the effect reverses between eras
Rules' average R per day, by SqueezeMetrics GEX regime (yesterday's GEX vs its one-year median):

| | Low gamma | High gamma |
|---|---|---|
| 2011–17 | −0.02 (656 days) | −0.07 (875) |
| 2018–20 | **+0.39** (368) | −0.07 (380) |
| 2021–26 | +0.11 (662) | **+0.31** (785) |

In 2011–20 the theory held: the rules did better when dealers were less long gamma. In 2021–26 it reversed: the rules did
better on HIGH-gamma days. So the published "long gamma kills momentum" story, as measured by this S&P-based number, does not
explain Argon's 2021–26 results. Possible reasons: GEX is an S&P measure, not Nasdaq; SqueezeMetrics' method may have
changed; or same-day options changed what the end-of-day number means after about 2022. None of these is tested here.

## What this batch says
Neither fix for 2026's whipsaw works. The whipsaw looks like something to survive (smaller size, skip-only, a stop rule),
not something to trade around. About 223 trials in total.
