---
type: scouted-idea
updated: 2026-10-19
built_from: 1487 days of prices (2021-01-04 to 2026-10-01)
---
# Over-tuned breakout

**Verdict:** rejected before testing

**Idea:** A deliberately over-tuned recipe, to show the critic stopping it.

**Source:** seed example

## Rejected by the critic before testing

- tries 36 settings; the limit is 12 (more tries = more chance of a lucky fluke)

## The recipe

```json
{
 "name": "Over-tuned breakout",
 "idea": "A deliberately over-tuned recipe, to show the critic stopping it.",
 "markets": [
  "NQ"
 ],
 "signal": {
  "type": "range_breakout",
  "minutes": [
   5,
   10,
   15,
   30
  ]
 },
 "filters": [],
 "stop": {
  "type": "atr",
  "frac": [
   0.1,
   0.2,
   0.3
  ]
 },
 "exit": {
  "type": "R",
  "mult": [
   1,
   2,
   3
  ]
 }
}
```

%% my notes below. Argon never changes anything under this line %%
## My notes

