---
type: scouted-idea
updated: 2026-10-19
built_from: 1487 days of prices (2021-01-04 to 2026-10-01)
---
# Ten-o-clock momentum

**Verdict:** not good enough

**Idea:** The first 30 minutes set the tone: follow the move from the open at 10:00.

**Source:** seed example

## Test on 5 years of real futures

2653 trades, +97.00R, worst drop -132.4R, Sharpe 0.32 (random entries: 0.01). First half +137.80R, second half -40.70R.

- ✅ at least 150 trades
- ✅ made money after costs
- ❌ made money in both halves
- ✅ Sharpe beats random entries (9/10)
- ❌ Sharpe of at least 0.5

## The recipe

```json
{
 "name": "Ten-o-clock momentum",
 "idea": "The first 30 minutes set the tone: follow the move from the open at 10:00.",
 "markets": [
  "NQ",
  "ES",
  "YM",
  "RTY"
 ],
 "signal": {
  "type": "time_momentum",
  "at": [
   "10:00",
   "10:30"
  ],
  "mode": "follow"
 },
 "filters": [
  "trend20"
 ],
 "stop": {
  "type": "atr",
  "frac": [
   0.15,
   0.3
  ]
 },
 "exit": {
  "type": "close"
 }
}
```

%% my notes below. Argon never changes anything under this line %%
## My notes

