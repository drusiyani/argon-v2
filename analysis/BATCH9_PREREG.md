# Batch 9 pre-registration (13 Nov 2026) — written and committed BEFORE any batch 9 code was run

Analysis only (does not touch the race). Dru asked for a deeper search for more profit. Trial count so far: about 160
ideas, so a lucky pass is likely; that is why every pass must hold in BOTH eras and the marks below cannot move.

Baseline = the FIXED package (batch 4/7). Pass mark for every idea, same as batches 5–8:
ADOPT only if, in BOTH eras (2021–26 and 2010–20), vs the fixed package: higher per-year return AND higher Sortino AND
worst drop no more than 1 point deeper AND bootstrap chance of a drop worse than −35% no more than 1 point higher
(1,000 draws, 63-day blocks, seed 20261111). Each idea is tested alone.

Ruled out before testing, on evidence: the 2–3am "overnight drift" (Boyarchenko, Larsen & Whelan). The authors' own July 2026
follow-up reports it was flat in 2021–25, so it cannot pass both eras.

## H1 — Regime tilt of the rules (mirror of the core)
Why: intraday momentum is stronger when volatility is high (Gao et al. 2018; Baltussen et al. 2021; Zarattini et al. 2024),
and the rules failed in the calm 2011–17 market. The core already shrinks when VXN is high; the rules would grow.
Rule: each trade of all four rules is sized 0.5 × min(1.5, VXN / median of its last 252 values), VXN read exactly as the
core reads it (one day early). No floor, no fitted constant.

## H2 — Overnight-after-a-down-day tilt
Why: Boyarchenko et al. find overnight returns are larger after sell-offs (dealers are paid to carry inventory overnight).
Rule: if the Nasdaq's regular session closes below its 9:30 open, hold an extra 0.5× long from that close to the next
session's 9:30 open. Cost 0.75 NQ pts per round trip. Skipped if either day is a roll or bad-data day, or |move| > 15%.

## H3 — Volatility-managed size for the whole package
Why: Moreira & Muir (2017) applied to the package itself: take more size when the package has been calm, less when rough.
Rule: k = min(1.5, median of the last 252 values of σ21 / latest σ21), where σ21 is the 21-day standard deviation of the
package's own daily return (before interest), using returns up to two days earlier. k = 1 until 60 values exist.
Daily return = k × (core + rules + pre-FOMC) + interest.

## H4 — Noise band in the European session (03:00–09:25 New York)
Why: Baltussen et al. find intraday momentum "everywhere", and this window is untouched by the four rules.
Rule (Nasdaq): P0 = the 03:00 open. Noise σ(m) = average |price(m)/P0 − 1| over the previous 14 eligible days (need ≥ 10).
At 03:30, 04:00 … 09:00: if flat and the last 1-minute close is above P0×(1+σ) → long at the next minute's open + 1 tick;
below P0×(1−σ) → short. If in a trade and the close is back inside the band → exit at the next open (re-entry allowed later).
Flat at 09:25. 1R = σ at entry × P0. Cost 1.25 NQ pts (0.75 + one extra tick each way for the thinner book).
Skip if cost > 0.10R. Skip roll and bad-data days. Size 0.5 × 1% risk, like the other rules.

## H5 — Learned day-quality sizing, trained on one era and tested on the other
Why: the "harder" route. A model can only be trusted on data it has never seen, so each era is judged with a model
trained ONLY on the other era.
Target: the four rules' total R that day. Features (all known by 9:30): VXN / its 252-day median (read one day early);
VXN 5-day change; |overnight gap| / ATR(14); previous day's |open-to-close| / ATR; Nasdaq 20-day return; rules' total R over
the previous 5 trading days. Model: ridge regression (λ = 1) on features standardised with the training era's mean and stdev.
Sizing: training-era predictions are cut into thirds; in the other era a day's rule trades are sized ×0.5 / ×1 / ×1.5
(times the usual 0.5) by which third its prediction falls in.
Pass: the batch mark above, with 2021–26 judged by the 2010–20 model and 2010–20 judged by the 2021–26 model.

## If anything passes
Passing ideas are combined and the combination must pass the same mark. Then, and only then, the leverage test from
lever.py (1.25×; worst drop shallower than −35% and under 20% of 21-day-block bootstraps below −35%, both eras).

## Not allowed after seeing results
No changing caps, windows, times, features, λ, sizes or pass marks. Diagnostics are reported but decide nothing.
