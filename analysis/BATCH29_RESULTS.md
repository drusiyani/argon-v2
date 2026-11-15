# Batch 29 results: "the unknown" (15–16 Nov 2026)

Rules and marks were committed first (`BATCH29_PREREG.md`, plus two addenda, each committed before its checks ran).
Format: return a year / Sortino / worst drop / crash chance. Running total: about 279 trials.

## Headline
1. **No new edge.** Ten unusual ideas plus one follow-up: none is an adopt candidate.
2. **The search found something more useful: how much of G3's headline was luck.** Adding three facts that carry no
   information at all moved G3's return by several points. The honest expectation for G3 is its jitter median:
   **+58.5% / 3.34 / −18.6% (2021–26) and +28.4% / 2.32 / −21.2% (2010–20)**, not +60.2% and +29.1%.
3. **G3 and skip-only cannot be told apart.** Differences under about 3 points (2021–26) or 1.5 points (2010–20)
   are inside the noise of the measurement.

## The ten ideas
| | 2021–26 | 2010–20 | Strict vs G3 | Luck (of 5,000) | Verdict |
|---|---|---|---|---|---|
| G3 (reference, single run) | +60.2% / 3.41 / −18.4% / 0.7% | +29.1% / 2.36 / −21.2% / 0.9% | | | |
| U1 noise band 5 min early (no model, vs package) | +57.6% / 3.18 / −20.6% / 1.8% | +20.3% / 1.69 / −21.9% / 7.8% | no (vs package) | | fail |
| U1 control: 5 min late | +55.7% / 3.17 / −20.5% / 0.9% | +22.4% / 1.80 / −22.6% / 6.4% | no | | |
| U2 sibling labels | +54.3% / 3.14 / −19.7% / 0.9% | +29.2% / 2.36 / −21.2% / 1.4% | no | 2 | fail |
| U3 QuantLab six-variant ensemble | +51.5% / 3.09 / −19.0% / 0.6% | +28.5% / 2.36 / −20.0% / 1.0% | no | | fail |
| U4 signal-candle shape | +60.7% / 3.48 / −18.7% / 0.6% | +29.4% / 2.38 / −21.2% / 0.9% | **yes** | 0 | fails check C (below) |
| U4b shape facts for every rule | +60.0% / 3.40 / −18.8% / 0.7% | +28.5% / 2.34 / −21.5% / 1.3% | no | 0 | fail |
| U5 recency weighting (3-year half-life) | +50.7% / 2.97 / −20.2% / 0.5% | +26.8% / 2.20 / −21.2% / 2.4% | no | 6 | fail |
| U6 longs ×0.75, shorts ×1.25 | +60.3% / 3.41 / −19.7% / 0.3% | +28.0% / 2.27 / −22.2% / 2.1% | no | 2,058 | fail |
| U7 night-heavy core (unlocked) | +57.1% / 3.30 / −17.7% / 0.3% | +21.0% / 1.78 / −26.3% / 7.5% | no | | fail |
| U8 model as a forecast for the core | not unlocked | | | | no rule tested |
| U9 plumbing calendar (5 flags) | none unlocked | | | | no rule tested |
| U10 news-candle trades | +54.6% / 3.12 / −19.8% / 1.3% | +28.3% / 2.29 / −21.2% / 1.2% | no | | fail |

## What each one showed
- **U1, the public clock.** Friction-free noise-band R a year, early / on the clock / late:
  2010–20: 5.0 / 7.4 / 8.7. 2021–May 2024: 14.3 / 12.9 / 13.3. Jun 2024–Nov 2026: **12.6 / 10.4 / 6.7**.
  After the May 2024 paper, being five minutes early beat being five minutes late by about 6R a year; before it there
  was no such gap (in 2010–20 late was better). That is the footprint a crowd on the :00/:30 clock would leave. It is
  2.5 years of data and the package test failed, so it is **logged as a watch item, not adopted**.
- **U2.** Sibling labels are 93% correlated with the trade's own label; almost no noise is removed. Worse in 2021–26.
- **U3.** The monthly pick has real skill in 2021–26 (35.3 vs 20.8 net R a year for the plain six-way average) and none
  in 2010–20 (4.0 vs 4.7). Averaging the six throws that skill away.
- **U4.** Passed the strict mark by half a point. Harder checks: junk-facts twin 0 of 300 (pass); double costs
  +56.0% vs +55.1% and +24.0% vs +23.6% (pass); sub-periods level-or-better in only 3 of 5 (2018–20: 68.1 vs 68.8,
  2021–25: 64.9 vs 66.1; **fail**, needed 4). Only one of the three facts is stable: where the candle closed within
  its range (weight positive in 88% of monthly refits). The trades whose call changed were no better than the ones
  they replaced. **Not adopted.**
- **U5.** Forgetting old trades faster hurt in both eras. The long history is helping, not hurting.
- **U6.** Shorts do hedge the core (daily correlation −0.28 / −0.24 vs +0.27 / +0.19 for longs), but in 2010–20 they
  earned a third of what longs did (+0.03R vs +0.10R), so leaning on them cost return and deepened the worst drop.
- **U7.** The Nasdaq's night leg has the better Sharpe in both eras (0.49 vs 0.33 in 2021–26; 1.20 vs 0.50 in 2010–20).
  Before switching costs a night-heavy core gave +60.2% / 3.44 / −17.6% and +31.1% / 2.52 / −21.2%. Switching twice a
  day costs more than it earns: fails at the pre-registered cost, and at half that cost it still would not beat G3's
  return in 2021–26.
- **U8.** Top-third forecast days were more volatile in both eras, but the Nasdaq's average move on them was lower in
  2021–26 (−4 bp vs +4 bp) and higher in 2010–20 (+4 bp vs 0 bp). No rule unlocked.
- **U9.** Pooled p-values: clock mismatch 0.32, VIX settlement 0.44, quarter end 0.80, after a holiday 0.83,
  **roll week 0.035** (kept trades averaged −0.06R in roll weeks vs +0.22R otherwise, worse in both eras). The bar was
  0.01 for five tests, so nothing unlocked. Roll week is logged as a watch item.
- **U10.** Following the 8:30 news candle loses: −0.13R and −0.11R a trade net, 42% and 38% winners, worse than the
  same rule on ordinary days. No drift to harvest after the first five minutes.

## Jitter test of our own recommendation (addendum 2)
Three pure-noise facts added to the 24, 300 runs each. Median (5%–95% range):

| | Return 2021–26 | Sortino | Worst drop | Return 2010–20 | Sortino | Worst drop |
|---|---|---|---|---|---|---|
| Package (no model) | +56.4% | 3.18 | −19.4% | +21.6% | 1.75 | −23.5% |
| G3, single run | +60.2% | 3.41 | −18.4% | +29.1% | 2.36 | −21.2% |
| **G3, jitter** | **+58.5%** (53.0 to 61.9) | 3.34 (3.08 to 3.50) | −18.6% | **+28.4%** (26.7 to 29.9) | 2.32 (2.20 to 2.43) | −21.2% |
| Skip-only, single run | +57.9% | 3.30 | −18.8% | +28.5% | 2.29 | −21.2% |
| **Skip-only, jitter** | **+57.8%** (52.9 to 61.6) | 3.30 (3.07 to 3.49) | −18.9% | **+28.8%** (27.7 to 30.0) | 2.32 (2.24 to 2.42) | −21.9% |

- G3 jitter runs beat the package in both eras on return 73% of the time, on Sortino 84%, and had a worst drop no
  deeper than the package 79% of the time. Skip-only: 75%, 84%, 59%.
- With the noise placed on QuantLab trades only (a harsher test): G3 median +56.2% / +26.8%, beating the package on
  return in both eras 48% of the time and on Sortino 65%. Skip-only: +54.6% / +27.5%, 28% and 42%.
- **Why so sensitive:** QuantLab's tight-stop trades have rare very large winners (a +10R trade is about 5% of the
  account at these sizes). Flip a handful of keep/skip calls and the yearly figure moves by points.
- **By the rules fixed in advance:** skip-only does not beat G3 on jitter medians in both eras, so **G3 stays the main
  book**; G3's Sortino improvement is robust (84% ≥ 80%). G3's quoted numbers become the jitter medians.

## What this means
- What the trade-selection model reliably adds over the package: about +2 points of return in 2021–26 and +7 in
  2010–20, a better Sortino, and a slightly shallower worst drop. That is the size of the edge found in 29 batches.
- The strict mark was resolving half-point differences that do not exist. Several earlier near-misses and near-passes
  (batches 24–28) were inside this noise. Future model comparisons should use jitter medians.
- More backtest tweaks will not find a bigger edge with this data: the yardstick is coarser than anything left to
  find. New information has to come from Race 1 itself (the AI desk) and from live paper trades.

## Watch items for the desk log (no rule attached)
1. Published-clock footprint (U1): track early-vs-late noise-band results live.
2. Roll week (U9).
3. Mega-cap pre-earnings freeze (S1, batch 26).
