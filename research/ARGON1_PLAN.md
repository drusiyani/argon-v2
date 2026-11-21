# Argon-1: our own forecaster, trained free on GitHub (plan, 21 Nov 2026)

**Question:** can a small model trained only for this job, for £0, match or beat the four frontier AIs at the 8:45 call?
Same target, same inputs cutoff and same scoring as the four seats. Shadow arm only: it never sizes a real trade in Race 1.

## What it predicts
- The existing label: **trend day** = |close − open| ≥ 0.6 × (high − low), NQ 09:30–16:00 New York. Half days not scored.
- Output: a trend chance (0–1). Size is then set by the same fixed cut-offs the market forecaster uses, so only the
  forecast differs between arms.

## What it sees (all before 08:45 New York, nothing later)
- 5-minute bars for NQ, ES, YM, RTY from the previous 18:00 open to 08:45 (the overnight session), plus the previous
  day's regular session.
- Daily context: VIX/VXN and its 1-year percentile, yesterday's range vs its 20-day average, calendar flags
  (FOMC, options expiry, jobs Friday). No headlines (that is what the frontier AIs add; keeping them out makes the
  comparison "price data only vs AI with news").

## Models (two candidates, one chosen by the rule below)
- **A, Kronos head:** Kronos-small (already in the repo, 24.7M parameters) kept frozen; its embedding of the overnight
  bars plus the daily context feeds a small trained classifier.
- **B, tiny from scratch:** a small transformer (about 60k parameters: 2 layers, width 48) on the same bars plus context.
- About 3,900 trading days exist for 2011–2026, which is small for deep learning. Expect a modest edge at best; a
  plain logistic regression (the Amendment 9 market forecaster) is the bar both must clear.

## Data split (fixed before training)
- **Train:** Jan 2011 – Dec 2020. **Validate:** Jan 2021 – Dec 2023 (choose A or B, and the stopping point).
- **Test once:** Jan 2024 – Oct 2026, opened a single time after the choice. Reported whatever it says.
- Then refit the chosen model on 2011 – Oct 2026 with the same settings and freeze it. Race 1 (forward days only) is the
  real test; every earlier period has been seen while building the rules, so backtests are reported, not trusted.
- Choice rule: the candidate with the better validation log-loss, provided it beats the market forecaster on
  validation; if neither does, Argon-1 is the better one anyway and the write-up says it failed validation.

## Training on GitHub Actions
- Runs in the private-data workflow pattern already used for booking (data pulled with `DATA_TOKEN`, never printed,
  never uploaded anywhere public). Standard Linux runner, CPU only.
- Each stage saves its output, so a failed or timed-out job resumes from the last finished stage. A full run is
  expected to take well under an hour (the dry run on synthetic data: features 16 s and Kronos 40 s per 220 days).
- Checkpoints and the final weights live in the private data repo (they are derived from licensed Databento data).
  Only the daily forecast is published.
- Fixed seed, pinned library versions, and the sha256 of the frozen weights written into `FROZEN.txt`.

## Live
- Runs inside the existing 8:45 desk job on the runner (no API cost). Logged as seat **argon1** with the others.
- Scored with the Amendment 13 two-step test and the Amendment 9 bootstrap, as a shadow arm, against: each AI, the
  council, the market forecaster, the one-line rule and the random sizer.

## Timeline (freeze 31 Jan 2027)
1. Late Nov: amendment written; feature builder + label builder; unit tests on synthetic data.
2. Early Dec: candidate A and B training on Actions; validation report.
3. Mid Dec: open the test period once; refit; freeze weights.
4. Jan: runs in the January practice with the four seats; reliability checked (it must answer every day by 09:25).
