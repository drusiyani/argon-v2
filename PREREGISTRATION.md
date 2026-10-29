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

## Amendment 2 (27 October 2026)

- **Risk per trade is now 0.75%** of the account (was 0.5%). One constant: `RISK` in `site/src/app1.js` and `engine/stats.py`.
- **New portfolio planned** (replacing the old main strategy + opening range): QuantLab first-candle/EMA rule, noise band,
  ATR band (all Nasdaq NQ) and the options-expiry reversal (NQ + ES). It goes into the engine only after the
  100-adjustment test below.
- **Honest limit on what the backtest can prove.** The four base strategies *and their settings* were chosen after seeing
  the whole history, including 2025–2026. So the 2025–2026 lockbox in `research/` only tests the **adjustments**
  (netting, sizing, loss limits, exits and so on), not the base portfolio. The only clean test of the base portfolio is
  the live paper trading from 1 January 2027.
- **Adjustment test, rules fixed in advance:** the list is in `research/ADJUSTMENTS.md`, committed before any test ran
  (the commit time proves it). Tested on Jul 2021–Dec 2024 only. Pass bars: combo Sharpe +0.10 over the baseline, better
  than the baseline in at least 3 of the 4 years, still better at double costs, and nearby settings also better. Survivors
  are opened on 2025–2026 **once**. Fail = out, no retries.
- Data fix: September 2026 minutes were duplicated in one loader (two overlapping files). Fixed, see `research/README.md`.

## Amendment 3 (28 October 2026): the v2 book, fixed before going live

- **The book:** QuantLab (NQ, *skips FOMC days*, the one adjustment that survived the lockbox), noise band (NQ), ATR band (NQ),
  options-expiry reversal (NQ + ES). 1R per trade each, **0.75%** of the account per trade. Code: `engine/portfolio.py`,
  logic in `research/common.py` (the exact tested code).
- **No daily loss limit.** With exact trade timing every version made results worse (`research/results/SUMMARY.md`).
- **Kill switch:** creating `data/KILL` stops new trades and the site shows the book as stopped. Emergency use only.
- **Shadow strategy, pre-registered now:** the same book with 12-month risk-parity weights. It runs alongside on paper and
  **never** changes the main book. Judged only on live paper results: after 12 months it replaces the main weighting only if its
  live Sharpe is higher *and* its live worst drop is no worse.
- **Freeze:** these rules freeze at **31 Dec 2026 23:59 UTC**. After that, nothing about the book changes until the
  12-month review, apart from the kill switch.
- Full-history backtest (mostly in-sample, read the honesty notes): $100k → $740,805, Sharpe 1.19, worst drop −26.5%,
  2026 −6.0%. Out of sample (2025-01 to 2026-09) Sharpe ≈ 0.65.
- Still to do before 1 Jan: feed this book's live signals (from the daily tape) into the desk so the agents judge these setups
  instead of the old main strategy's.

### Amendment 3b (28 October 2026): round 2 + a second lockbox
- 17 adjustments and their nearby settings registered in `research/ADJUSTMENTS2.md` **before any round-2 test code exists**,
  after a 5-member council review. Tested on Jul 2021 - Sep 2026, then the survivors **and the base book** are opened once on
  a never-seen 2011-2020 lockbox (`data/lockbox2010/`, bought 28 Oct 2026, $26.17, checked on timestamps only).
- If the base book fails on 2011-2020, nothing changes: it still goes live on 1 Jan 2027 and the result is published.

### Amendment 3c (28 October 2026): roll-day bug fixed
- The engine's roll-day list was always **empty**: Databento switches contracts at 8pm New York, which belongs to the next
  session, and the engine only counted a switch between two sessions. So QuantLab and the ATR band never skipped roll days,
  despite the stated rule. Fixed in `research/common.py` (every contract switch marks its session).
- Effect on the v2 book (full history): Sharpe 1.19 → **1.16**, $100k → **$689k** (was $741k), worst drop −26.5% → −24.4%,
  double costs 1.01 → 0.98. 11 QuantLab and 9 ATR-band trades removed. The noise band has its own loader and was unaffected.
- This is a code fix to match an already-stated rule, not a tuning change. Round 1's lockbox verdict for Q24 was computed before
  the fix and is not re-run (one shot means one shot); round 2 uses the fixed code for both the baseline and every adjustment.

### Amendment 3d (28 October 2026): risk 1% per trade
- Risk per trade is now **1%** (was 0.75%), by Dru's choice, before the 31 Dec freeze. One constant: `RISK` in
  `site/src/app1.js` and `engine/stats.py`, `risk_pct` in `engine/portfolio.py`. Sharpe in R is unchanged; size of swings is not.
- Full history at 1% (with the roll-day fix): $100k → **$1.13M**, about +59% a year, worst drop **−32%**, 2026 −7.1%; double costs $680k.

### Amendment 3e (28 October 2026): QuantLab dropped, cost rule added
- After lockbox 2, 8 structural variations were compared on all eras (2011-17, 2018-20, 2021-26) with a selection rule
  committed **before** running (`research/variations.py`, results `research/results/VARIATIONS.md`): highest worst-era Sharpe,
  double-cost Sharpe at least the base's, ties to the simpler one. Picked **V5: drop QuantLab + skip any trade whose cost is over
  10% of 1R.** This is in-sample (every year has now been seen); the clean test is live from 1 Jan 2027.
- No variation made 2011-2017 profitable (best −0.54). The book is a bet that the post-2018 regime continues.
- New book, Jul 2021 - Sep 2026 at 1%: see data/portfolio.json. Risk-parity shadow continues on the new book.

### Amendment 3f (28 October 2026): keep QuantLab (Dru's choice, V4)
- Dru chose **V4: all four strategies + the 10%-of-1R cost rule** over the selection rule's pick V5 (drop QuantLab), after
  seeing both. Logged openly as a hindsight choice: V4 made more in both eras (2011-20: $92.7k vs $74.6k from $100k; 2021-26:
  $1.19M vs $282k at 1%) but with bigger drops (−70%/−32% vs −65%/−24%). QuantLab's gains are concentrated in a few big-news
  months (2024: +61R of its +77R came in July and November).
- The desk page (docs/desk.html) is embedded in the site as a preview with sample data.

## Amendment 4 (28 October 2026): the desk becomes a morning day-type forecaster (shadow test)
Designed after a 6-member council review (statistician, risk manager, trader, AI engineer, sceptic, methodologist).
- **Job:** every weekday 8:45-9:25am New York, before the open, forecast whether today is a TREND day or a CHOP day and pick a
  size for the whole v2 book: 0.5x / 1x / 1.5x. It never picks direction. Inputs are only things known before 9:30: overnight
  move and range, yesterday's range vs its 20-day average, 5-day RSI (dealer-gamma clue), VIX and its 1-year percentile,
  calendar (FOMC, options expiry, jobs Friday) and market headlines. Code: `engine/daytype.py`.
- **Three arms, all on paper from 1 Jan 2027, none changes the real book:** (1) 1x, (2) dumb rule: yesterday's range / 20-day
  average > 1.2 -> 1.5x, < 0.8 -> 0.5x, else 1x, (3) AI forecast. A day never risks more than 4R in total (size x trades <= 4).
- **AI rules:** model pinned to `claude-sonnet-5-5`, temperature 0, asked 3 times, MEDIAN size used; prompt frozen, fingerprint
  `8b27b11cc4cadeba`; it reads no self-written lessons. Veto only for: breaking_unscheduled_event, market_halt, data_feed_broken, and only if
  2 of 3 runs agree. Not finished by 9:25 -> counts as 1x (logged as late).
- **Scoring:** `engine/daytype_score.py`: Sharpe of each arm (monthly R), plus the Brier score of the AI's trend probability
  against whether the book made money before costs that day.
- **Promotion rule:** after **at least 120 scored trading days**, the AI arm takes real control only if its Sharpe beats
  **both** other arms by **at least +0.15**. Otherwise it stays shadow and the result is published either way.
- **Any change to the model, prompt, inputs or rules restarts the 120-day clock.**
- The separate per-setup desk (Scout / Sceptic / Risk / Chief judging the original strategy's setups) continues as its own
  experiment, scored against "take every setup". It does not touch the v2 book.
