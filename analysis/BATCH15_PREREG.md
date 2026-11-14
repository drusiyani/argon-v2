# Batch 15 pre-registration (14 Nov 2026) — written and committed BEFORE any batch 15 code was run

Analysis only (does not touch the race). Dru asked to look "deeper and wiser". Batch 14 showed that more searching of this
data has stopped paying. So this batch asks different questions: WHY do the patterns exist, WHAT happens if we are wrong,
and HOW MUCH should be bet on the part that works. About 200 trials so far.

## Part A — Mechanism, measured on the index itself (diagnostics, no pass mark)
No rules and no trades are involved, only daily open/high/low/close of the Nasdaq and S&P futures, in three periods
(2010–17, 2018–20, 2021–26).
1. "A trend day is followed by a sideways day": the next day's move size (|open→close| / ATR) and straightness
   (|open→close| / (high − low)) after the top fifth of days by move size, against all other days.
2. "The day follows the overnight gap": average open→close return in the direction of the gap, for all days, for days where
   the gap goes AGAINST yesterday's open→close direction, and for days where it goes WITH it.

## Part B — Gap-continuation trade (new trades, not resizing). Runs only if Part A.2 supports it
Condition: on the Nasdaq, the average open→close return in the gap's direction on "gap against yesterday" days is above
zero in all three periods.
Trade: on those days, enter the Nasdaq future in the gap's direction at the 09:31 open, exit at the 15:54 close. No stop.
Size 0.5× of equity (notional). Cost 0.75 points per round trip. Skip roll days and bad-data days.
Marks: (1) alone, positive return and Sharpe ≥ 0.3 in BOTH eras (the edges.py mark); (2) only then, package + the trade must
meet the growth mark from batch 13. Lineage: this idea comes from the batch 11–12 scans, so it is not blind.

## Part C — How much to bet on the rules (a risk dial, not a new edge)
Leverage on the whole package keeps failing because the Nasdaq core carries the crash risk. This tests more weight on the
model-sized rules only, core unchanged at 1×: rules weight 0.5 (today), 0.75 and 1.0, all with the batch 14 model (W1m).
Judged by the growth mark. The answer is the largest weight that meets it.

## Part D — What if we are wrong? (diagnostics, reported whatever they show)
For core only, today's package, and the model-sized package at each weight from Part C: return a year and worst drop in
2013–17 (the rules had no edge at all), 2018–20, 2021–25 and 2026 so far (the edge is fading).
The 2013–17 column is the estimate of what each choice costs if the edge disappears.

## Not allowed after seeing results
No changing the weights tested, the trade's times or size, the conditions, or the marks.
