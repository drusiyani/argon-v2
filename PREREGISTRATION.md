# Argon v2 pre-registration: can an AI trade?

Written and committed **before** the AI desk has any scored decisions. The commit that adds this file, and its
timestamp in the GitHub history, is the proof of when it was written. Nothing below may change after that commit;
any later change has to be a new, dated section at the bottom, and the original stays as it is.

## What is frozen (from 20 October 2026)

- **Strategies:** the main strategy (London session, settings re-picked monthly from the previous 6 months) and the
  opening-range breakout on the Nasdaq (settings re-picked monthly, 20-day trend filter allowed). No new strategies,
  settings or filters are added to these. New ideas go to the research scout's separate "explorer" track only.
- **Costs and fills:** limit orders fill only if price trades one full tick through; stops slip 1 tick (3 ticks in
  the first 15 minutes of the US session); real per-market costs on every trade; no trading on contract roll days,
  no new trades 8:25-8:40 New York, flat by 1:55pm on Fed decision days and 3:55pm on other days.
- **The AI desk:** four Claude prompts with separate jobs and separate memories (Scout, Sceptic, Risk on
  claude-haiku-5-5; Chief on claude-sonnet-5-5). The prompts in `engine/agents.py` at this commit are frozen. Each
  agent rewrites its own lessons every Friday; that is part of the design, declared here in advance.
- **Risk:** 0.5% of the paper account per trade.

## The question and the hypotheses

**Main question:** do the setups the AI desk chooses to take do better than simply taking every setup the rules find?

- **H1 (main):** the average result of setups the desk takes is higher than the average of all setups.
- **H2:** the desk's picks beat the rules-only trader over the same days.
- **H3:** the desk's picks beat Kronos-small's direction calls on the same setups.
- **H4:** the desk's picks beat buying and holding the Nasdaq over the same months.

## How it will be measured

- **Period:** 1 January 2027 to 31 March 2027, live, forward only (an AI can't be fairly tested on the past).
- **Unit:** every setup the rules flag is played out to its result whether the desk takes it or not.
- **Test for H1:** difference in average R (taken minus all), with a 95% confidence range from a **day-clustered
  bootstrap** (every setup from the same day, across all markets, is resampled together), 10,000 resamples.
- **Minimum sample:** no verdict unless **at least 100 desk decisions** are scored. Fewer than 100 by 31 March means
  the result is reported as **"inconclusive: not enough decisions"**, whatever the numbers look like.
- **Verdicts:** *yes* if the whole 95% range is above zero; *no* if the whole range is below zero; otherwise
  *can't tell*. Reported exactly like that, even if it's disappointing.
- **Also reported, not tested:** how often the four agents disagree (if almost never, they are effectively one
  opinion); the desk's results in R and in dollars on whole micro contracts; Sharpe, Sortino and worst drop.

## What the agents' explanations are worth

The desk is scored on its **decisions** only. The agents' written reasons and weekly lessons are recorded as text and
treated as ideas to test, not as evidence.


## Freeze record

- **Frozen at commit** `cdefedc2715294c25842c50fedc0548ce6cc4ae2` (20 October 2026). The rules, costs, prompts and model versions above are the ones in that commit. GitHub's history shows its timestamp and that nothing above this section has changed since.

## Amendment 1 (20 October 2026)

- The freeze is **lifted** at Dru's request, so changes can still be made. Every change from now is logged in the changelog.
- Before the AI experiment starts, the rules will be **frozen again** with a new freeze record here. The evaluation window (1 January to 31 March 2027), the tests and the N ≥ 100 rule above stay exactly as written.
- The forward test only counts from the date of the new freeze.
