---
type: rules
version: 0.5
locks_on: 2026-11-24
live_from: 2026-12-01
---
# Rulebook v0.5

The current rules, in plain English. Every month the settings are re-picked from whatever worked best over the previous 6 months (see [[Lessons]] for why that's not a guarantee). Every change is written in the [[Changelog]].

## [[The main strategy]]

1. **Pick a level.** It has to be an important one: a [[Session levels|session level]], a 15-minute or hourly high or low, or two near-equal highs or lows.
2. **Wait for a sweep.** Price must poke past it and close back within 10 minutes, during London 2–5am and New York 8:30–11:30am.
3. **Day's direction:** hourly trend must agree.
4. **Markets disagree ([[SMT]]):** not required.
5. **Trend flip.** Within 40 minutes, with a big candle.
6. **Entry.** Wait for price to come back to the [[Price gap (FVG)|price gap]] (or the order block if there's no gap). Give up after an hour, or if price hits the target first.
7. **Risk rules** (from Argon v1, can't be switched off): the target must be worth at least 1.5× the risk, no more than 5 trades a day, stop for the day after losing 2R, one trade per market at a time.

Stop loss just past the sweep. Target: the next important level on the other side, if it's worth at least 2× the risk. Markets: Nasdaq and S&P 500. Everything closes at 3:55pm.

## [[The order-block strategy]]

Buy or sell the first time price comes back to a fresh 15-minute order block, if the hourly trend agrees. Markets: gold only. Session: New York 8:30–10am only. Same risk rules.

## Settings Claude is allowed to change

- **entry**: fvg_first, ob_first, ob_only
- **windows**: both, ny, london
- **bias**: none, h1, pd, h1_pd
- **smt**: required, optional
- **pool**: quality, any
- **markets**: all, nq, nq_es
- **target**: pool, 2R, 3R

## Still unknown

- The site decides on 5-minute candles. Faster charts (1 or 2 minutes) might work better; 2-minute data only goes back to 2026-09-08.
- Big news releases (like 8:30am US data) aren't filtered out yet.

%% my notes below. Argon never changes anything under this line %%
## My notes

