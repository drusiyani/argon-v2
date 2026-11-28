# Argon strategy lab

A nightly loop. Ideas go in `ideas/NNN-name.md`, results in `LOG.md`. Nothing here changes the live book:
a passing idea is only flagged, and Dru decides. After the 31 Jan 2027 freeze, passes go to Race 2.

Rules for every idea:
- Read `TRIED.md` first. No repeats or close variants.
- Written down BEFORE any test: exact entry, exit, size, costs, and the pass bar.
- Discover on 2011-2020 only. Confirm ONCE on 2021-2026. Must improve the book's Sharpe in BOTH eras.
- Must be testable with the data we have (1-minute NQ/ES prices, daily VIX/VXN, calendar, daily gold + 10y Treasury futures from 2010).
- Each test adds one to the trial count, which raises the bar for everything.

Gemini drafts one idea each morning (Gemini app scheduled action). If it's good, Dru opens it as a GitHub issue titled
`Gemini idea: <name>`. Every night Claude runs `NIGHTLY.md`: tests the oldest open idea, or proposes its own if there is none.
