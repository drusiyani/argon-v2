# Batch 30 pre-registration: core / rules split under G3 (16 Nov 2026)

Written before any code ran. Batch 17 moved the rules weight with the core fixed at 1x. The split between the two has
never been tested. Daily return = c x (VXN-managed core + pre-FOMC tilt) + T-bill interest + k x 1% x G3 rules R.

Grid (fixed): core c in {0.25, 0.5, 0.75, 1.0}; rules weight k in {0.5, 0.625, 0.75, 1.0}. 16 mixes, 15 new trials
(total about 294). Reference: c = 1, k = 0.5 (G3: +60.2% / +29.1%).

Marks (fixed):
- **Strict-risk winner:** among mixes whose worst drop is no more than 1 point deeper than G3's and whose crash chance
  (drop worse than -35%, 1,000 draws, 63-day blocks, seed 20261111) is no more than 1 point higher, in BOTH eras:
  the one with the highest return in its worse era. It must beat G3's return in both eras to count.
- **Growth-limit winner:** same, but worst drop up to 5 points deeper than G3 and never riskier than the Nasdaq alone
  (drop -35.1% / -28.6%, crash chance 35.3% / 8.3%).
- Reported for every mix: return, Sortino, worst drop, crash chance, and 2026 actual return and worst drop.
Notes: single-run G3 figures carry about 1.7 points of luck in 2021-26 (batch 29 jitter test); a winner by less than
3 points (2021-26) or 1.5 (2010-20) is inside the noise and will be reported as such. No other mixes will be tried.
