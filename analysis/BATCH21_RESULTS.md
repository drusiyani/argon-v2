# Batch 21 results (14 Nov 2026): the QuantLab hold leg passes alone, fails in the package, and is not adopted

Pre-registration: `BATCH21_PREREG.md` (committed before the run). Code: `batch21_dump.py`, `batch21.py`. Raw: `batch21.json`.

## Mark 1 — alone at 1× notional: PASS
| | 2021–26 | 2010–20 |
|---|---|---|
| Return a year / Sharpe / worst drop | +11.5% / 0.66 / −20.4% | +9.3% / 0.68 / −27.2% |
| Days traded / share of winning days | 1,390 / 52.5% | 2,492 / 50.2% |

## Mark 2 — in the package at 0.5×: FAIL (strict mark)
Each cell: return a year / Sortino / worst drop / bootstrap chance of a drop worse than −35%.

| | 2021–26 | 2010–20 | Strict | Growth |
|---|---|---|---|---|
| Package | +56.4% / 3.18 / −19.4% / 1.0% | +21.6% / 1.75 / −23.5% / 7.4% | — | — |
| Package + leg | +63.8% / 3.26 / −20.8% / 0.7% | +26.7% / 1.96 / −25.1% / 10.2% | no | no |
| Skip-only | +57.9% / 3.30 / −18.8% / 0.8% | +28.5% / 2.29 / −21.2% / 2.4% | — | — |
| Skip-only + leg | +65.4% / 3.34 / −24.3% / 2.8% | +33.9% / 2.51 / −20.9% / 2.4% | no (2021–26 drop 5.5 points deeper) | no |

It adds return in both eras but also deepens the drops, so it is more exposure, not a free improvement. Not adopted.

## Why it should not be trusted much
- **Three years carry it.** Average return per day (t-statistic): 2010–17 +1.3 bps (0.7); 2018–20 +10.3 (2.5);
  2021–25 +2.4 (0.7); 2026 +18.4 (3.0). By year only 2018, 2020 and 2026 are large; most years are near zero.
- **It fails on the S&P.** 2010–17 −3.0 bps a day (t −2.0), 2018–20 +3.2, 2021–26 +0.5. Not positive in all three periods.
- **It is the same bet as the rules.** Correlation with the rules' daily result is 0.33–0.38.
- Batch 20's lesson applies: one narrow pass after about 230 tries is weak evidence.

## What it settles about the "shaken out" idea
On days the stopped QuantLab trade lost, the hold leg lost too: −13.9 bps a day in 2021–26 (t −3.8), −6.9 in 2010–20.
On days it won, the leg made +51 and +59 bps. So when the stop is hit, the direction was usually wrong for the rest of the
day as well. Claude's 14 Nov explanation of 2026 ("right direction, stopped out first") was wrong, which is also why the
second-chance re-entry (batch 18) lost.

## QuantLab before the cost rule (diagnostic)
Picked trades on all signal days, R before costs / after costs / share the cost rule removed:
2011 −70 / −121 / 80%; 2012 −64 / −121 / 91%; 2013 −44 / −106 / 97%; 2014 −22 / −67 / 90%; 2015 +11 / −26 / 89%;
2016 +13 / −27 / 89%; 2017 −3 / −42 / 87%; 2018 +26 / +6 / 28%; 2019 +88 / +66 / 39%; 2020 +4 / −7 / 5%;
2022 +42 / +34 / 2%; 2023 +48 / +39 / 1%; 2024 +68 / +59 / 5%; 2025 +36 / +30 / 0%; 2026 (to 12 Nov) +12 / +8 / 0%.
QuantLab's result before costs rose from clearly negative (2011–14) to a peak in 2024 and has fallen by about half in each
year since. The cost rule kept it almost entirely out of the book before 2018.
