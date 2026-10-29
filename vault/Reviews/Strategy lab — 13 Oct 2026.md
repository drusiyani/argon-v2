---
type: lab-run
week: 2026-W42
versions_tried: 1305
passed: 2
---
# Strategy lab — 13 Oct 2026

> [!info]
> Practice days: up to 2026-09-18, split into two halves at 2026-08-26. Exam days: everything after 2026-09-18, used once. To pass, a version must make money in both halves of the practice days (over 20+ trades), then make money on the exam days (8+ trades), and survive a bad-luck test where its trades are shuffled 2,000 times (worst drop must stay under 12R).

## Result

1,305 versions tried → 10 made money in both practice halves → 5 best picked → 2 passed the exam. So Rulebook v1.0 keeps the same rules, plus the risk rules from Argon v1.

## The five best

| settings | practice | exam | worst drop | result |
|---|---|---|---|---|
| entry ob_first, windows both, bias pd, smt optional, pool any, markets all, target pool | +17.62R (25 trades) | -1.00R (29) | -7.35R | failed |
| entry ob_only, windows both, bias pd, smt optional, pool any, markets all, target pool | +17.62R (25 trades) | -3.03R (28) | -7.46R | failed |
| entry fvg_first, windows both, bias pd, smt optional, pool any, markets all, target pool | +12.61R (25 trades) | -2.79R (28) | -8.4R | failed |
| entry ob_first, windows both, bias pd, smt optional, pool any, markets all, target 3R | +9.89R (23 trades) | +3.48R (32) | -8.4R | passed |
| entry ob_only, windows both, bias pd, smt optional, pool any, markets all, target 3R | +9.89R (23 trades) | +2.40R (31) | -8.4R | passed |
| old rules (v0.2) | +0.61R (14) | -0.11R (20) | – | for comparison |

Why, in plain English: [[Lessons]]. Current rules: [[Rulebook v1.0]].

%% my notes below. Argon never changes anything under this line %%
## My notes

