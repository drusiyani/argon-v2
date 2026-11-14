# Batch 19 results (14 Nov 2026): no better ranking found; at double costs only skip-only stays inside the Nasdaq limits

Pre-registration: `BATCH19_PREREG.md` (committed before the run). Code: `batch19.py`. Raw: `batch19.json`.

## Part A — Skill: none of the four alternatives beats the current model in all three periods
Out of sample, average R after costs of the top third / bottom third / gap:

| Model | 2013–17 | 2018–20 | 2021–26 | Beats M0 in all three? |
|---|---|---|---|---|
| M0 ridge (current) | −0.015 / −0.107 / **0.091** | +0.176 / −0.114 / **0.290** | +0.178 / −0.011 / **0.190** | — |
| M1 per-rule | 0.104 | 0.178 | 0.118 | no |
| M2 win/loss | 0.100 | 0.069 | 0.037 | no |
| M3 clipped target | 0.097 | 0.175 | 0.057 | no |
| M4 ridge + boosting | 0.104 | 0.381 | 0.151 | no (loses 2021–26) |

M0 stays. Notably, the models that ignore the size of wins (M2, M3) lose most of the skill in 2021–26: what the model
learns is which trades can produce the big winners, not which trades win more often.

## Part B — Double costs (decides the main book)
Each cell: return a year / Sortino / worst drop / bootstrap crash chance. Growth mark against today's package at NORMAL costs,
as pre-registered. Nasdaq-alone limits: drop −35.1% / −28.6%, crash chance 35.3% / 8.3%.

| | 2021–26 | 2010–20 | Growth mark |
|---|---|---|---|
| Package today, normal costs (reference) | +56.4% / 3.18 / −19.4% / 1.0% | +21.6% / 1.75 / −23.5% / 7.4% | — |
| Package today, double costs | +49.9% / 2.87 / −20.2% / 1.4% | +13.1% / 1.14 / −30.5% / 31.3% | no |
| Skip-only, double costs | +52.6% / 3.05 / −19.7% / 1.0% | +21.6% / 1.79 / −25.9% / 7.7% | no (return not above the normal-cost package) |
| Skip-and-press, double costs | +65.6% / 3.38 / −22.4% / 4.2% | +23.2% / 1.80 / −25.9% / 16.0% | no (2010–20 crash chance above the Nasdaq's) |

**By the pre-registered rule: neither meets the growth mark at double costs.**

Two honest notes on reading this:
- The rule compared double-cost versions with the package at NORMAL costs. That puts the whole cost increase against the
  candidates, so it is a harsh test (Claude's design choice, flagged after seeing the results; not changed).
- One failure does not depend on that choice. Skip-and-press at double costs has a 16.0% chance of a drop worse than −35% in
  2010–20, about twice the Nasdaq's 8.3%. Skip-only stays inside both Nasdaq limits (−25.9% vs −28.6%; 7.7% vs 8.3%), and
  against today's package at the same double costs it is better on every measure in both eras.
- Today's frozen package is the most cost-sensitive of the three: at double costs its 2010–20 crash chance is 31.3%.
