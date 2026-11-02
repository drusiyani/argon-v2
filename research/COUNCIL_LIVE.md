# Council review: the live paper-trading engine (Task 1), 2 Nov 2026

Written and committed BEFORE `engine/live.py` was built. The design under review is in the handover (section 9):
a nightly run on Databento 1-minute data, the exact `research/common.py` code, micro contracts at 1% risk,
an append-only hash-chained ledger, a position check, a kill switch, plus an unofficial live view from Yahoo.

## The reviewers

**1. Quant researcher**
- Running the whole history every night through `portfolio.book()` is the only honest way to get "the same code". Good.
- The walk-forward re-pick only looks at finished months, and every indicator (ATR, sigma, EMA) only looks backwards, so
  yesterday's trades must come out *identical* tonight. Make that a check, not a hope: re-derive every booked day each run.
- Databento sometimes revises old bars. If a re-derived day differs, never silently rewrite the ledger. Stop and alert.

**2. Execution trader**
- Rounding down to whole micros shrinks risk. ATR band stops can be 250+ NQ points ($500+ per MNQ), so at $100k some
  trades get 1 contract and some get **zero**. Zero-size trades must be logged as skipped, with the reason, not vanish.
- Micro commissions are bigger per point than full contracts (roughly 1.5x the research cost in points).
  Keep the official book on the research costs so it stays comparable, and let the double-cost ledger be the stress case.
- Record the fill price the rules assumed (entry and stop), so live fills could be compared later.

**3. Software engineer**
- Idempotent: running twice books nothing twice. Unique trade id `strategy|symbol|date|entry minute|variant`.
- Never book a day with incomplete data. A day is only booked when every market's data reaches past 16:00 New York.
- Rolls are found from all four markets' days, so the nightly download must fetch NQ, ES, YM **and** RTY,
  or roll days silently disappear (the `B5` day intersection). Test it.
- Record the code commit and each market's last bar in every ledger entry.

**4. Risk manager**
- Kill switch checked before anything else, and a killed run books nothing.
- Every run: open positions after the close must be zero (all strategies are flat by 15:55). Anything else = halt.
- Sanity cap on contracts per trade, so a data glitch (tiny risk) can't size 5,000 micros.

**5. Statistician / auditor**
- Pre-register what "consistent with the backtest" means NOW, as fixed numbers: the 5th-95th percentile range of
  every rolling k-month sum (k = 1..12) of the book's monthly R, Jul 2021 to Sep 2026. Hash it in the pre-registration.
- It's a flag, not a stop rule. And say plainly the backtest is mostly in-sample, so the band is optimistic.

**6. DevOps**
- GitHub runs cron jobs hours late. A separate nightly workflow with two schedules (22:15 and 02:30 UTC), sharing the
  `argon-v2-writer` lane, plus catch-up, makes late or missed runs harmless.
- Alerts via ntfy.sh with the topic in a secret (`NTFY_TOPIC`), for: failed run, mismatch, kill switch, missed morning call.

**7. Product / site**
- The live view must say **unofficial** everywhere it appears. The nightly ledger always wins.

**8. Sceptic**
- Yahoo's NQ=F rolls on its own timetable, is delayed and has gaps, so the live view will sometimes disagree with the
  ledger. That is expected. Don't let anyone (including Dru) treat the live view as the record.
- Practice from mid-November on real days, so the first real bug happens in a practice ledger, not on 2 Jan 2027.

## Verdict: build it, with these changes
1. Replay check every run: every booked day is re-derived and must match the ledger exactly; else halt + alert.
2. Data gate: only book a day when all four markets' data reaches past 16:00 New York.
3. Fetch all four markets nightly (rolls). Test that the downloader lists all four.
4. Zero-size and cost-rule skips are logged in the ledger with reasons.
5. Official book on research costs; double-cost ledger alongside.
6. Contract cap per trade (200 micros).
7. "Consistent with backtest" band pre-registered as `research/results/live_band.json`, sha256 in Amendment 6.
8. Practice ledger from 16 Nov 2026 in `data/ledger_practice/`; the official ledger starts 1 Jan 2027 and stays empty until then.
