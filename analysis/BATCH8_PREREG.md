# Batch 8 pre-registration (13 Nov 2026) — written and committed BEFORE any code was run

Analysis only (does not touch the race). Goal: find something that makes money when the package loses, so the
package can carry more size without failing the crash test. Two new rules, then one leverage re-test. Nothing else.

## Rule S1 — Nasdaq/S&P spread reversion (market-neutral)
- Days: regular sessions present in BOTH NQ and ES. Skip roll days (either), bad-data days (either), FOMC decision days.
- Hedge ratio β: OLS slope of NQ open-to-close log returns on ES open-to-close log returns, previous 60 eligible days (need ≥ 40).
- Spread: x(t) = ln(NQ_t / NQ_open) − β · ln(ES_t / ES_open), 1-minute closes, open = first regular minute's open.
- Scale σ: root-mean-square of the end-of-day spread over the previous 20 eligible days.
- Entry: check each 15-minute close from 10:14 to 14:59. The first time |x| ≥ 1.0σ, enter at the next minute's open,
  short the rich leg and long the cheap leg (β-weighted). One trade per day.
- Exits (checked on 1-minute closes): stop when |x| ≥ 2.0σ on the same side; target when x crosses 0; otherwise 15:55.
- 1R = 1.0σ. Costs: NQ 0.75 pts + β × ES 0.5 pts per round trip, plus 1 extra tick per leg on stops. Skip if cost > 0.10R.
- Size in the package: 0.5 × 1% risk, the same weight the four rules get.

## Rule S2 — Calm-day fade (Nasdaq)
- Days: only when yesterday's VXN (known before yesterday's close, as in the package) is below its trailing-252-day median.
  Skip roll, bad-data and FOMC days.
- Session average price A(t) = running mean of the 1-minute typical price (H+L+C)/3 since 9:30 (no volume in the loader).
- Band = 0.35 × daily ATR(14) (previous 14 days).
- Entry: check each 15-minute close from 10:14 to 14:59. First close ≥ A + band → short; ≤ A − band → long, at the next minute's
  open ∓ 1 tick. One trade per day.
- Stop = entry ± band (1R). Target = A at the entry minute (fixed). Otherwise flat at 15:55. Stop slippage 1 tick.
- Costs 0.75 NQ pts. Skip if cost > 0.10R. Size in the package: 0.5 × 1% risk.

## Pass mark for S1 and S2 (same as batches 5–7)
ADOPT only if, in BOTH eras (2021–26 and 2010–20), package + rule vs the fixed package baseline has:
higher per-year return AND higher Sortino AND worst drop no more than 1 point deeper AND bootstrap chance of a drop worse than
−35% no more than 1 point higher (batch 7 bootstrap: 1,000 draws, 63-day blocks, seed 20261111).

## Leverage re-test (only if S1 and/or S2 pass)
Package + the passing rule(s) at 1.25×, judged by the leverage test exactly as in lever.py (11 Nov): PASS if, in BOTH eras,
historical worst drop shallower than −35% AND under 20% of bootstrapped histories (21-day blocks, 1,000 draws, seed 20261111)
have a drop deeper than −35%. If neither rule passes, there is no leverage re-test and the package stays as it is.

## Not allowed after seeing results
No changing thresholds (1.0σ / 2.0σ / 0.35 ATR / 60 / 20 days), times, sizes, or the pass marks. Diagnostics (correlation,
standalone stats) are reported but decide nothing.
