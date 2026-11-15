# Batch 29 pre-registration: "the unknown" (15 Nov 2026)

Written and committed before any Batch 29 code ran. Reference book is **G3** (batch 24):
+60.2% / Sortino 3.41 / worst drop −18.4% / crash chance 0.7% (2021–26) and +29.1% / 2.36 / −21.2% / 0.9% (2010–20).

Dru's brief: look where nobody else would look. Three places have never been examined in ~264 trials:
1. the **public clock** of the published noise-band strategy (is a crowd arriving at the same minute?),
2. the strategy's **own sibling trades** (variants that were computed every day and thrown away),
3. the **seams of the book** (day vs night, long vs short, the trade model as a forecast for the core) and the
   market's **plumbing calendar**.

## Marks (fixed now)
- **Strict mark vs G3**: return and Sortino both better in BOTH eras, worst drop no more than 1 point deeper,
  crash chance (drop worse than −35%, 1,000 draws, 63-day blocks, seed 20261111) no more than 1 point higher.
- **Luck test** where a random twin exists: 5,000 random versions (same number of changes, shuffled within each year);
  fewer than 5% may beat the idea's return in both eras.
- Nothing is adopted from a diagnostic. A diagnostic can only unlock one rule that is written below.
- An idea that fails is not re-tuned in this batch.

## Tests

**U1. Front-run the published clock.** The noise band decides on bars closing at :00 and :30, the same clock as the
May 2024 paper. E5 moves every decision 5 minutes earlier (:55 / :25); L5 moves it 5 minutes later (:05 / :35) as the
control. Nothing else changes (8 variants, monthly re-pick, cost rule).
- Diagnostic: friction-free noise-band R a year for E5 / base / L5 in 2010–20, 2021–May 2024, Jun 2024–Nov 2026.
  The crowd story predicts E5 − L5 turns positive only after May 2024.
- Mark: package with E5 (no model) passes the strict mark against the baseline package in both eras AND E5 beats L5 on
  return in both eras. Only then is G3 rebuilt on the E5 book and judged strict vs G3.

**U2. Sibling labels.** G3 learns from each trade's own friction-free result, which is very noisy. U2 trains the same
model on the average friction-free points result of all variants of the same rule that entered on the same day, minute
and side ("siblings", including itself), divided by the trade's own stop distance. Features, monthly walk-forward,
both skip tests: unchanged. Mark: strict vs G3 + luck test.

**U3. Sibling ensemble (QuantLab).** Diagnostic: did the monthly pick beat the plain average of the six variants
(friction-free and net, by era)? Rule: trade all six variants at one sixth size each (each under the cost rule), using
G3's keep/skip call for that day's QuantLab trade. Mark: strict vs G3. (Top-2 and top-3 were tested in round 2: W01.)

**U4. Shape of the signal candle.** Three new facts for QuantLab trades from the five 1-minute bars inside 9:30–9:35
(zero for other rules): where the candle closed within its range (signed by trade side); share of the candle's net
move made in its last minute (clipped to ±2); log of last-two-minutes volume over first-two-minutes volume.
Added to the 24 features, G3 pipeline otherwise unchanged. Mark: strict vs G3 + luck test.

**U5. Recency weighting.** G3 with each training trade weighted 0.5^(age in years / 3). Mark: strict vs G3 + luck.

**U6. Long/short balance.** Shorts tend to pay on the core's bad days. Under G3: long momentum trades ×0.75, short
×1.25. Mark: strict vs G3 + luck test (random ×0.75 / ×1.25 labels, same counts within each year).

**U7. Day vs night core.** Diagnostic: Nasdaq return, volatility and Sharpe for the night leg (16:00 → 9:30) and the
day leg (9:30 → 16:00), both eras. Rule, tested only if night Sharpe beats day Sharpe in BOTH eras: core ×1.25 at
night and ×0.75 by day, paying 1.25 NQ points per contract-equivalent switched. Mark: strict vs G3.

**U8. The trade model as a forecast for the core.** Diagnostic: split days by G3's first prediction of the day into
thirds of its trailing 252 values; report the Nasdaq's move from that entry to the close (mean and volatility) per
third, both eras. Rule, tested only if top-third days show lower mean AND higher volatility than bottom-third days in
BOTH eras: core ×0.75 from that entry to the close on top-third days, same switching cost as U7. Mark: strict vs G3.

**U9. Plumbing calendar.** Five flags never examined: (a) weeks when US and European clocks are out of step;
(b) VIX settlement mornings; (c) last trading day of a quarter; (d) the week of the quarterly futures roll (Monday to
Friday containing the second Thursday of Mar/Jun/Sep/Dec); (e) first trading day after a US market holiday.
Diagnostic: average friction-free R of G3-kept momentum trades on flag days vs other days, with a permutation p-value
(10,000 shuffles of the flag across days within each year), pooled and per era. A flag unlocks a skip rule only if
pooled p < 0.01 (five tests) AND flag days are worse in both eras; the skip rule is then judged strict vs G3.

**U10. News-candle trades (new trade source).** On CPI, Employment Situation, PPI, Retail Sales and GDP mornings
(ALFRED release dates, 8:30 ET): take the 8:30–8:35 candle, enter at its close in its direction, stop at its far end,
exit at 9:25 or the stop. Pre-market friction doubled (1.5 points + 2× tick slippage); cost rule 0.10R; same size as
other rules. Placebo: the identical rule on every non-release day.
- Mark 1: average net R positive in both eras, and release days beat placebo days (permutation p < 0.05, pooled).
- Mark 2: added to G3, strict mark in both eras.

## Honesty notes
- About 14 new trials; running total about 278. Both eras have been seen many times; nothing here is blind.
- U1's "after May 2024" window is 2.5 years. A pass there alone proves nothing and cannot be adopted.
- U9 has small samples by construction (some flags are 4 days a year).
- If nothing passes, G3 stays the recommendation and this batch is reported as a null result.

---
## Addendum (16 Nov 2026), written after the first Batch 29 run and before any of the checks below ran
First run: nine of ten ideas failed. **U4 (shape of the signal candle) passed the strict mark, but by a hair**
(+60.7% vs +60.2% and +29.4% vs +29.1%). The luck test it passed compares the whole model with random skipping, which G3
already passes; it does not show that the three new facts add anything. So U4 gets harder checks before it counts.

**Check A, junk-facts twin (the real luck test for an add-on).** 300 runs of the U4 pipeline in which the three shape
facts are shuffled among QuantLab trades within each year, so they carry no information. U4 keeps its pass only if
fewer than 5% of junk runs match or beat U4's return in both eras. Also reported: how often junk runs beat G3 on
return, Sortino and worst drop in both eras (the false-pass rate of the strict mark for a three-fact add-on).

**Check B, double costs.** With every trade's cost doubled, U4 must still beat G3 on return in both eras.

**Check C, sub-periods.** Return a year for G3 and U4 in 2010–13, 2014–17, 2018–20, 2021–25, 2026. U4 must be at
least level with G3 (within 0.1 points) in four of the five.

**Reported, no mark:** trades whose keep/skip call changed (count and average net R), and the sign of each new fact's
weight across the monthly refits.

U4 is an adopt candidate only if A, B and C all pass.

**U4b (one new trial, total about 279).** The same three facts for every rule, measured on the five 1-minute bars before
the entry minute (for QuantLab that is the same 9:30–9:35 candle). Marks: strict vs G3; junk-facts twin as in Check A
(shuffled among all trades within each year, 300 runs, under 5%); and it replaces U4 only if it also beats U4 on
return and Sortino in both eras.

Also logged for the write-up, no rule attached: the U1 clock footprint (early minus late, friction-free R a year) and
the roll-week result from U9 (p = 0.035, short of the 0.01 bar).

---
## Addendum 2 (16 Nov 2026): jitter test of our own recommendation. Written before it ran.
What the U4 checks showed by accident: adding three facts that carry NO information moved G3's return by several
points (junk-run median +56.4% / +27.0% when the junk sat on QuantLab trades; +59.1% / +28.3% when spread over all
trades; G3 itself +60.2% / +29.1%). So (1) the strict mark cannot resolve differences of a point or two, and (2) G3's
own headline may sit at the lucky end of what a G3-type model delivers. This has to be measured properly.

**Jitter test.** For G3 and for skip-only: 300 runs each with three pure-noise facts (standard normal) added to the
24, (i) on every trade, (ii) on QuantLab trades only (zero elsewhere). Nothing else changes. Reported per era:
median and 5%–95% range of return, Sortino and worst drop; share of runs beating the plain package on return, and on
Sortino, in both eras.

**What it can change (fixed now):**
- The "honest expectation" quoted for a model book becomes its jitter median (version i), not its single headline run.
- The main-book recommendation moves from G3 to skip-only only if skip-only's jitter median beats G3's on BOTH return
  and Sortino in BOTH eras (version i). Otherwise G3 stays.
- If under 80% of G3 jitter runs beat the package on Sortino in both eras, G3's risk improvement is reported as
  not robust.
This is a check on an existing result, not a new idea; it adds no trial to the count.
