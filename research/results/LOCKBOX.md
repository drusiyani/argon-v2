# Lockbox (opened once, 2026-10-28)

The single survivor of the 109 pre-registered adjustments was run once on the locked months, Jan 2025 to Sep 2026.

| | Sharpe | R | 2025 | 2026 (to Sep) | Sharpe, double costs |
|---|---|---|---|---|---|
| Baseline (4 strategies) | 0.52 | +52.5R | +57.1R | −4.5R | 0.45 |
| **Q24: QuantLab skips FOMC days** | **0.65** | **+64.8R** | +63.4R | +1.4R | **0.59** |

**Verdict: KEEP.** It beat the baseline at normal and double costs, as pre-registered.

## Honest notes
- 1 of 109 passing is about what luck alone could produce, so the lockbox pass matters more than the test-window gain. It's still only 21 months.
- The baseline itself fell from Sharpe 1.41 (2021–2024) to 0.52 (2025–2026). The edges are decaying or 2026 is unusually choppy. Expect long flat stretches live.
- Exact-time daily loss limits all **hurt** (−2R: −0.11 Sharpe). The earlier +0.09 from the daily-total simulation came from its lookahead. Dropped.
- Risk parity (P13) raised Sharpe by +0.26 but failed the "better R in most years" bar, because it moves weight to the low-volatility legs and makes less R. That bar compares R, not risk-adjusted R, which is a flaw in my rule. It was not rescued: changing the rules after seeing results is exactly what the lockbox exists to stop. Any retest would need a fresh pre-registration and new data (live).
- A crash-check during setup printed results for 15 adjustments before the full run. The list was already committed, so nothing could change, but it is disclosed here.
- The 4 base strategies were chosen after seeing 2025–2026, so this lockbox only tests the adjustment. The clean test of the portfolio is live from 1 Jan 2027.
