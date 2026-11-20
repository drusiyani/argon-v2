# Batch 34 results: is G3 real once every test is counted? (20 Nov 2026)

Rules: `BATCH34_PREREG.md` (commit 3d50cad, before the run). Code: `batch34.py`, `batch34_power.py`. Output: `batch34.json`,
`batch34_power.json`. Analysis only; nothing in the race changes until an amendment says so.

## A. Deflated Sharpe (is G3 better than zero after ~299 tries?): FAIL as registered, pass on the fairer reading
| | 2021-26 | 2010-20 |
|---|---|---|
| G3 Sharpe (a year) | 1.76 | 1.41 |
| Luck bar, N = 299, spread of ALL saved trials | 1.45 | 1.15 |
| Deflated Sharpe probability, N = 299 (pass mark 0.95) | **0.79** | **0.81** |
| Same, N = 50 | 0.95 | 0.95 |
| Same, N = 299, spread of package-level trials only | 1.00 | 1.00 |

The registered test fails: the saved trials range from "index alone" (Sharpe ~0.5) to package variants (~1.8), and that
wide spread sets a high luck bar. Counting only the trials G3 was really picked from (package variants), it passes easily.
Honest reading: G3's Sharpe is very unlikely to be pure luck, but the strict version of the test does not prove it.

## B. Is G3's gain over the plain package real? FAIL
| | 2021-26 | 2010-20 | pooled |
|---|---|---|---|
| Extra return a year | +2.0% | +5.7% | +4.4% |
| t (Newey-West) | 0.55 | 2.40 | 2.20 |
| Bootstrap p | 0.29 | 0.007 | 0.013 |

Bars: 3.59 for the best of 299, 3.09 for the best of 50. Pooled t = 2.20 clears neither. In the era G3 was built on,
its gain is indistinguishable from zero. As registered: G3 stays the main book, but the write-up must say its gain over
the package is not proven.

## C. The four rules before and after May 2024 (when the noise-area paper was published), 2021-26 era
| rule | before: trades, mean R, t | from May 2024: trades, mean R, t |
|---|---|---|
| QuantLab | 671, +0.12, 1.44 | 598, **+0.20, 1.79** |
| Noise band | 495, +0.08, 1.63 | 392, +0.05, **0.78** (flagged) |
| ATR band | 486, +0.08, 2.65 | 351, +0.04, 0.95 |
| Expiry | 76, +0.29, 2.45 | 56, +0.11, 0.78 |

Every rule except QuantLab weakened after May 2024. Since then QuantLab made 122R of the four rules' 161R; the other three
are near zero, and for each of them the best 10 days made more than their whole total. Matches NostroBenJ's finding that
the noise-area breakout faded after publication (NQ Sharpe 1.49 -> 0.88, ES 1.78 -> -0.19).

## D. Power of the desk's promotion rule (added after A-C; not pre-registered)
Simulated on G3's rules sleeve. "Skill" = how well the AI's size tracks the day's result (AUC 0.50 = none, 0.54 = small,
0.58 = clear).

| rule | 120 days: no skill / small / clear | 230 days: no skill / small / clear |
|---|---|---|
| Today's rule (Sharpe beats both arms by +0.15) | **23%** / 48% / 66% | **17%** / 49% / 77% |
| Shuffle test (beats 95% of its own sizes reshuffled) | 5% / 25% / 63% | 6% / 37% / 88% |

Today's promotion rule promotes an AI with no skill about one time in five, and finds a small real skill only about
half the time: close to a coin flip. The shuffle test keeps false promotions at 5% and is better at catching clear skill.
Recommendation for the freeze: replace the +0.15 rule with the shuffle test, and say in advance that ~230 days can only
detect a clear skill, not a small one.
