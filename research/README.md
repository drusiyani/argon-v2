# research/

Rebuilt, saved copies of every test so a sandbox reset can't lose them again.

- `orig_qb.py`, `orig_deep.py`: the original QuantLab and deep-dive (noise band = part B) scripts, unchanged apart from ROOT, output paths and one data fix (below).
- `common.py`: the 4 portfolio strategies rebuilt with trade-level output + walk-forward + scoring helpers.
- `strat_quantlab.py`, `strat_noiseband.py`, `strat_atrband.py`, `strat_expiry.py` write `results/trades_*.csv` (date, entry time, exit time, side, R).

## Reproduction check (full history, `ARGON_FULL=1`)
| strategy | expected | rebuilt |
|---|---|---|
| QuantLab NQ (walk-forward) | 1,355 trades, +176.7R, Sharpe 0.83 | 1,355, +176.7R, 0.83 ✓ |
| Noise band NQ (walk-forward) | 859 trades, +52.0R, Sharpe 0.71 | 859, +52.0R, 0.71 (0.70 over 63 months, first month has no trades) ✓ |
| ATR band NQ | 828 trades, +50.7R, Sharpe 1.00 | 828, +50.7R from Jan 2021; 766 / +43.8R inside the Jul 2021–Sep 2026 window; Sharpe 1.00 ✓ |
| Expiry NQ / ES | 65 trades each, +14.1R / +9.0R | 65 / +14.1R, 65 / +9.0R from Jan 2021 (60 each inside the window) ✓ |

## Data bug found and fixed (2026-10-27)
`data/databento/NQ_2026-09.csv.gz` overlaps `NQ_2026-partial.csv.gz` (both hold September 2026). The deep-dive loader read
both, so every September 2026 minute was counted twice (noise band came out 862 trades / +51.5R). Both loaders now keep one
bar per minute, which gives back the original 859 / +52.0R. `engine/backtest_core.py` already de-duplicates.

## Lockbox
Nothing from 2025-01-01 on is simulated unless `ARGON_LOCKBOX=open` (survivors, once) or `ARGON_FULL=1` (only for the base
reproduction above, numbers that were already public).
