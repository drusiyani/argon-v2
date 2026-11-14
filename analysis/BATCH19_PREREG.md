# Batch 19 pre-registration (14 Nov 2026) — written and committed BEFORE any batch 19 code was run

Analysis only (does not touch the race). Dru asked to "find skill": a better ranking of trades, not more size. The auditor
(14 Nov) found that skip-and-press's gain over skip-only is mostly size; the model's ranking adds only about 2 points.
About 223 trials so far; this adds 4 models and one cost check.

## Part A — Four alternative models (same 24 features as W1m, same monthly walk-forward, same ≥ 500 training trades,
## same cut-points: thirds of the training predictions)
- **M0** ridge on R, λ = 100 (the current model, W1m). The reference.
- **M1 per-rule:** a separate M0 for each of QuantLab, noise band and ATR band (≥ 300 training trades each, else M0's size).
- **M2 win/loss:** L2 logistic regression predicting "R after costs > 0" (C = 0.01, standardised features). Ignores how big
  the win is, so the few huge QuantLab winners cannot dominate the fit.
- **M3 clipped target:** M0 trained on R clipped to [−1, +3], for the same reason.
- **M4 ensemble:** average of M0's prediction rank and the batch 13 boosting model's prediction rank (HistGradientBoosting,
  depth 3, 200 rounds, learning rate 0.03, 100 per leaf, seed 0), each ranked within its own training set.

## Skill score (decides)
Out of sample, average R after costs of the top third minus the bottom third, in 2013–17, 2018–20 and 2021–26.
A model **beats M0** only if its gap is larger than M0's in ALL THREE periods.

## Package check (decides between models that beat M0)
Skip-and-press (bottom third skipped, top third ×1.5) at rules weight 0.5 with that model. It must beat the M0 version on
return AND Sortino in both eras, with an average trade size no larger than M0's in either era (so the gain is skill, not size).
If several pass, the one with the largest average gap wins. If none pass, M0 stays.

## Part B — Double-cost check (decides the main book, as agreed with Dru on 14 Nov)
Skip-only and skip-and-press (M0, weight 0.5) with every trade's cost doubled, scored by Dru's growth mark against today's
package at normal costs:
- If skip-and-press meets the growth mark at double costs → it can be the main book (skip-only becomes the shadow).
- Otherwise skip-only is the main book, provided it meets the growth mark at double costs; if neither does, that is reported.

## Not allowed after seeing results
No changing models, settings, cut-points, the skill rule, the package rule or the cost multiple.
