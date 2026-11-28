# Nightly lab run (Claude) — the procedure

Run by a scheduled Claude session every night. Up to FIVE strong ideas per night (each its own batch, pre-registration and
results file). Fewer is fine: never pad the night with weak ideas, since every trial raises the bar. Nothing here may touch the live book,
PREREGISTRATION.md, the engine, the desk or the site.

## 1. Pick the idea
1. Queue, in this order: open issues labelled `lab` (oldest first), then open `Gemini idea: ...` issues (oldest
   first), skipping any marked "none tonight". Take up to five from the queue.
2. If the queue gives fewer than five, you may propose up to the rest yourself (only ideas that survive every filter;
   zero is a fine answer) using exactly the Gemini filters in `lab/gemini_idea.py` (PROMPT):
   read `lab/TRIED.md` and `lab/LOG.md`, generate 5 candidates, kill the weak ones. If none survive, add a line to
   `lab/LOG.md` ("none tonight: <why>"), push, and stop. Do NOT burn a trial on a weak idea.
3. Sanity-check the chosen idea against `lab/TRIED.md` and every `analysis/BATCH*_PREREG.md`. If it is a repeat or
   close variant, comment on the issue why, close it, log it, and stop.

## 2. Pre-register (commit BEFORE running anything)
- Next batch number NN = highest `analysis/batchNN.py` + 1.
- Write `analysis/BATCHNN_PREREG.md`: source (issue link), exact rules, costs (real ticks, same as batch 40/41),
  pass bar, and "not allowed after seeing results". Pass bar (fixed): the rules book's Sharpe with the idea added must
  beat the book alone in BOTH eras (lockbox2010 = 2011-2020 and databento = 2021/22-2026), after costs.
- Ideas that add a NEW market or sleeve (e.g. issue #2, trend sleeve) are compared on the FULL book (core + four rules
  + idea vs core + four rules), because their point is to diversify the core, not the rules.
- Luck check (reported for every idea, not part of the pass bar): paired block bootstrap of the Sharpe gain, 21-day
  blocks, 2000 draws, both eras. Report the share of draws where the gain is <= 0, and the trial count. A PASS whose
  era-2 luck share is above 0.10 is labelled "PASS (weak, could be luck)".
- Commit and push it on its own first.

## Extra data (daily, both eras)
- `data/extra/GC_daily.csv.gz` (gold) and `data/extra/ZN_daily.csv.gz` (10-year Treasury): Databento ohlcv-1d,
  continuous front month, Jun 2010 - Oct 2026. They load into `data/extra/` with the other private files. Read them
  directly (not via ARGON_DATA) in both eras. Merge Sunday-evening bars into the next weekday. Prices are not
  back-adjusted: on an `instrument_id` change, set that day's return to 0 and charge 1 tick of roll cost.

## 3. Code and run
- `analysis/batchNN.py`, modelled on `analysis/batch40.py` / `batch41.py` (use `research/common.py` helpers and
  `analysis/batch38.py` `rules_daily()` / `stats()`). Must run under `ARGON_FULL=1` with `ARGON_DATA=lockbox2010`
  and the default databento era. Write `analysis/batchNN_<era>.json`.
- Workflow: copy `.github/workflows/batch41.yml` to `batchNN.yml` and swap the number with sed. Push, then dispatch:
  `gh api -X POST repos/drusiyani/argon-v2/actions/workflows/batchNN.yml/dispatches -f ref=main`
- Heavy data work runs ONLY in GitHub Actions (the private data repo is never read in the sandbox, never sent to any
  outside tool). Wait for the run (poll `gh run list -w batchNN.yml -L 1`), pull, read the json.
- If the run errors, fix the code (not the rules) and rerun; note every rerun in the results file.

## 4. Report
- `analysis/BATCHNN_RESULTS.md`: table (own Sharpe both eras, book Sharpe with it vs alone, trades, avg R after
  costs), verdict PASS / REJECTED, one paragraph of plain-English why.
- Add the idea to the right section of `lab/TRIED.md` (and bump the trial count), add a line at the top of
  `lab/LOG.md`, comment the verdict on the issue and close it.
- A PASS is only flagged ("PASS — for Dru to decide"); never change the live book.
- Phone alert if the `NTFY_TOPIC` is reachable via a workflow, otherwise skip (the issue comment notifies Dru).

## House rules
- Push routine: `git checkout -- docs/data/brain.json docs/data/graph.json`, add, commit, then
  `git pull -q --rebase --autostash origin main || (git checkout --ours docs/index.html && python3 engine/build_front.py && git add docs/index.html && GIT_EDITOR=true git rebase --continue)`,
  then `git -c push.negotiate=true push -q origin HEAD`.
- Never put API keys or Dru's email anywhere. Plain English, short sentences in results files.
