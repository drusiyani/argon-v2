# Argon v2

> **Current state (Nov 2026).** The book is four pre-registered intraday strategies on Nasdaq and S&P futures (QuantLab, noise band,
> ATR band, expiry reversal), tested on Databento 1-minute data. Paper trading starts **1 January 2027**; the rules freeze
> **31 Dec 2026 23:59 UTC**. See `PREREGISTRATION.md` for every rule change.
>
> - **About 2011–2020:** that data was sealed until 28 Oct 2026, opened once, and has been used since for comparisons, so it is
>   **no longer an independent test**. The book lost money on it.
> - **The official live book** is `engine/live.py`: every night after the close it runs the exact backtest code on that day's
>   Databento data and appends to a hash-chained ledger in `data/ledger/` (practice runs from 16 Nov 2026 in
>   `data/ledger_practice/`). Workflow: `.github/workflows/live.yml`. The 5-minute live view on the site and desk
>   (`engine/live_view.py`, Yahoo bars) is **unofficial**; the ledger is the record.
> - Handy commands: `python engine/holding.py` (what am I holding?), `python engine/replay.py 2026-10-16` (replay any day),
>   `python engine/alert.py "title" "msg"` (test the phone alert; needs the `NTFY_TOPIC` secret).
>
> Everything below this box describes the original v2 (the liquidity-sweep farm and the retired agent desk) and is kept for history.

A research site that tests a liquidity-sweep trading strategy on the same markets as Argon v1's Kronos indices bot: Nasdaq, S&P 500, Dow and Russell 2000 futures, with no real money. Big players often push price just past obvious highs and lows to trigger stop orders, then reverse. Argon v2 finds those moments, decides whether to trade them, and keeps a record of every decision and result.

Goes live on **1 January 2027**, but only if it passes the success criteria shown on the site.

## What's in here

| Folder | What it is |
|---|---|
| `engine/fetch_data.py` | Saves the day's futures prices (Yahoo only keeps ~60 days, so we keep our own copy) and the monthly 1-minute history from HistData |
| `engine/farm.py` | The "farm": replays recent days, logs every level, sweep, trend flip, gap and order block, and every trade taken or skipped |
| `engine/backtest_core.py`, `engine/lab.py` | The long backtest (Jan 2024 onwards, every trade checked minute by minute) and the monthly re-pick of the rules |
| `engine/extra.py` | Strategies from published research: the opening-range breakout (Zarattini & Aziz, SSRN 4416622), with real futures costs and settings re-picked monthly |
| `engine/fast.cpp` | The speed-critical parts in C++: reading the 1-minute history (with New York daylight-saving maths), building 5-minute candles, and walking every trade minute by minute. Builds itself with `g++` the first time it's needed; set `ARGON_NO_CPP=1` to use the pure-Python versions, which give identical results (checked candle-for-candle) |
| `engine/build_site.py` | Builds `docs/index.html` |
| `site/src/` | The site itself: Overview, Chart (with a TradingView view), Studies, Events and Lab |
| `engine/brain.py` | Grows the Obsidian vault every run (see below) |
| `engine/reflect.py` | Claude's weekly reflection note (needs an `ANTHROPIC_API_KEY` secret) |
| `vault/` | The brain. Open this folder in Obsidian as a vault |
| `.github/workflows/argon.yml` | Runs everything automatically |

## How it runs

- **Every weekday after the US close:** save the tape, run the farm, rebuild the site and the notes.
- **On the 2nd of each month:** add last month's 1-minute data, rerun the long backtest, and re-pick the rules from whatever did best over the previous 6 months.
- **First run:** downloads all the history (takes a while).

To run it by hand: Actions → Argon v2 farm → Run workflow.

## The desk (AI agents)

Four AI agents (Scout, Sceptic, Risk, Chief) judge every setup the rules find, about 2 to 3 a day, live. Each has its own memory in `data/agent_memory/` and its own note in the vault, and rewrites its own lessons every Friday. Every setup is played out either way, so the desk's picks are scored against taking everything and against the busier rules-only trader.

- Runs every 15 minutes in the London and New York sessions (`.github/workflows/desk.yml`).
- Needs the `ANTHROPIC_API_KEY` secret. Scout, Sceptic and Risk use Claude Haiku 5.5; the Chief, who makes the final call, uses Claude Sonnet 5.5. About 40–60p a month. Change them with the `ARGON_AGENT_MODEL` and `ARGON_CHIEF_MODEL` variables.
- It only works forward, never on old prices: an AI has already read about the past.
- Before every call, each agent is briefed on the rest of Argon: what the order-block and opening-range strategies are doing in that market, every trade already open across all strategies, whether the strict main rules would take it, and Kronos's forecast.
- **Kronos:** v2 runs its own **Kronos-small** (24.7M parameters, free CPU) every 15 minutes during the sessions and writes `data/kronos.json`; the bots read it before every call. Optionally, to use v1's Kronos instead, have Argon v1 publish its latest forecast as a small JSON file, e.g. `{"NQ":{"direction":"up","confidence":0.62,"horizon":"1h","updated":"2026-12-01T14:30Z"}, "ES":{...}, "YM":{...}, "RTY":{...}}`, then add its web address as a repository variable or secret called `KRONOS_URL`. Until then the agents are told Kronos isn't available.
- Keep the repo **public** if you can: GitHub Actions is free for public repos, but a private repo's 2,000 free minutes a month won't cover a desk that runs every 15 minutes.

## Real futures data (Databento)

Without it, the long backtest uses free CFD prices for the Nasdaq and S&P 500 only. With it, the backtest uses real CME futures 1-minute candles for all four markets (NQ, ES, YM, RTY) back to 2021.

1. Make a Databento account. New accounts get $125 of free credit, which should cover this many times over.
2. Copy your API key from the Databento portal.
3. In this repo: Settings → Secrets and variables → Actions → New repository secret. Name: `DATABENTO_API_KEY`.
4. Actions → Argon v2 farm → Run workflow → mode `backfill`.

The script checks the price before it downloads anything and stops if it would cost more than $50 (the calculator estimate for all four markets back to 2021 was about $40, covered by the free credit).

## The brain

`vault/` grows every run and never deletes anything:

- **Piles up:** a note for every day, trade, month and lab run.
- **Living notes:** each market, level, session and question is re-measured from all the data every run. When a finding moves, it's written into that note's history.
- **Your notes are safe:** anything under the line `%% my notes below… %%` at the bottom of a note is never changed. Claude reads it in its weekly reflection.
- **Home.md** shows how big the brain has got.

To get it on your phone or laptop, use the Obsidian Git plugin pointed at this repo, so new notes arrive and yours get pushed back.

`vault/Dashboards/` has Obsidian Bases tables: every trade with totals by strategy, the losses to learn from, and the brain's current answer to each question.

**Working on the vault with Claude Code:** install Obsidian's official skills (MIT licence, by Obsidian's CEO Steph Ango) so Claude writes proper Obsidian notes, callouts and Bases:

```
/plugin marketplace add kepano/obsidian-skills
/plugin install obsidian@obsidian-skills
```

## Turn on the website

Settings → Pages → Deploy from a branch → `main`, folder `/docs`.

## Honest status

Over 27 months of testing, adjusting the rules monthly beat fixed rules, but neither strategy has shown a reliable profit yet. The forward test before launch decides whether it goes live.

## Data

- Futures: Yahoo Finance (CME NQ, ES, RTY and CBOT YM), 5- and 2-minute bars
- History: HistData.com 1-minute CFD prices for Nasdaq and S&P 500 (NSXUSD, SPXUSD). The Dow and Russell only have the futures history the workflow saves each day.
- Raw data is not in this repo. Databento's licence forbids republishing CME data, and HistData publishes no licence to redistribute its files, so both live in the private repo `drusiyani/argon-data`. Each folder keeps a public `MANIFEST.json` (file names, sizes, SHA-256). To reproduce a result, get your own copies (Databento is paid; HistData is a free download) into `data/`, then run `python engine/verify_data.py` to check they match byte for byte.
- Charts: TradingView Lightweight Charts (Apache 2.0)
