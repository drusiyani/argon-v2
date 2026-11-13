# Batch 11 (13 Nov 2026): attribution of the package, and the overnight-gap test (FAIL by the rule, narrowly)

Pre-registration: `BATCH11_PREREG.md` (committed before the package test). Code: `batch11.py`. Raw: `batch11_*.json`.

## Part 1 — Attribution (diagnostics, no pass mark)

**Where the package's return comes from (arithmetic % a year, rules at half size)**

| Piece | 2021–26 | 2010–20 |
|---|---|---|
| VXN-managed Nasdaq core | 12.3 | 18.4 |
| Pre-FOMC tilt | 3.9 | 1.1 |
| T-bill interest | 3.3 | 0.6 |
| QuantLab | 17.7 | 2.0 |
| Noise band | 5.0 | −0.2 |
| ATR band | 4.7 | −0.9 |
| Expiry reversal | 2.4 | 0.8 |
| (costs inside the rule lines) | −4.3 | −7.2 |

**The rules are a "lose a little most days, win big on wild days" bet.** On the Nasdaq's worst 5% of days they made +2.0% a
day (2021–26) and +1.2% (2010–20); on its best 5% of days +1.2% and +0.7%; on the ordinary 90% of days they lost 0.04% and
0.10% a day.

**The break is 2018, not 2021.** The three momentum rules, R before / after costs, by year:
2010 −8/−11, 2011 −4/−20, 2012 +8/−5, 2013 −9/−21, 2014 −4/−17, 2015 +3/−7, 2016 −4/−17, 2017 +12/−1,
2018 +78/+61, 2019 +35/+19, 2020 +49/+37, 2021 +40/+33, 2022 +65/+57, 2023 +79/+68, 2024 +97/+89, 2025 +60/+53, 2026 +20/+16 (to 12 Nov).
Eight years with no edge even before costs, then nine winning years in a row, five of which (2018–20, 2025–26) were never
used to pick the rules. Volatility does not explain the break: 2015, 2016 and 2019 had the same average daily range
(1.4% of price) and only 2019 made money. That is why every volatility or day-type filter "splits the decades".

**The edge is shrinking.** After costs: 2024 +89R, 2025 +53R, 2026 +16R so far, and −5R since July 2026. Two of the five
deepest package drops in 2021–26 were caused mostly by the rules, both in the last 12 months
(Nov 2025–Jan 2026 and July 2026).

**Drops:** the two deepest in 2021–26 (both 2022) came from the core. In 2010–20 they were shared between core and rules.

## Part 2 — Overnight-gap direction (found by looking; see the pre-registration)

Trades with the gap / against it, average R after costs: 2010–17 +0.02 / −0.13; 2018–20 +0.12 / +0.03; 2021–26 +0.13 / +0.05.
With the gap was better in 13 of 17 years and for each rule in each period (9 of 9).

Each cell: return a year / Sortino / worst drop / bootstrap chance of a drop worse than −35%.

| | 2021–26 | 2010–20 | Verdict |
|---|---|---|---|
| Package baseline | +56.4% / 3.18 / −19.4% / 1.0% | +21.6% / 1.75 / −23.5% / 7.4% | — |
| K1 with-gap ×1.5, against ×0.5 | +65.7% / 3.46 / −20.5% / 2.6% | +27.8% / 2.08 / −20.7% / 4.0% | FAIL (2021–26: drop 1.1 pts deeper, limit 1.0; crash chance +1.6, limit +1.0) |
| K2 skip against-gap trades | +49.7% / 3.01 / −24.3% / 6.0% | +28.3% / 2.32 / −18.2% / 0.2% | FAIL (passes 2010–20 only) |

K1 raised return, Sharpe and Sortino in both eras and cleanly passed the sealed decade, but missed two risk marks in 2021–26
by small margins. K1's average size was about 1.06×, which may account for it; a size-neutral re-run was NOT done because
that would be tuning after seeing the result. No leverage test counts. Status: candidate for a shadow book in Race 1.
