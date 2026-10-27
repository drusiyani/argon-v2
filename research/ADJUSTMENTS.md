# Argon v2: pre-registered adjustments

109 adjustments, written down **before any test ran** (this commit's timestamp is the proof). Generated from `research/adjustments.py`; `research/run_all.py` tests exactly these.

## Rules (fixed in advance)

- **Baseline:** QuantLab (walk-forward, 6 variants) + noise band (walk-forward, 8 variants) + ATR band + expiry (NQ+ES), each 1R per trade, summed.
- **Test window:** Jul 2021 to Dec 2024 (42 months). 2025-01 onward is the **lockbox**, not simulated at all.
- **Same realism as always:** costs NQ 0.75 / ES 0.5 pts, stop slippage, roll days skipped, flat 3:55 (1:55 on FOMC days), monthly re-pick from the previous 6 months.
- **Pass bars** (all must hold): combo Sharpe at least **+0.10** over baseline (raised from +0.05 because of ~100 trials); better than baseline in at least **3 of the 4 years** (2021 H2, 2022, 2023, 2024); still at least **+0.05** better at **double costs**; every **nearby setting** at least +0.05 better.
- **Risk levels (S)** can't change a Sharpe measured in R, so they are reported (yearly return, worst drop, halving chance), not passed or failed.
- **Lockbox:** Survivors are run ONCE on 2025-01..2026-09. Pass = Sharpe above the baseline at normal AND double costs. Fail = out.
- **Honesty note:** the 4 base strategies and their settings were chosen after seeing 2025-2026, so the lockbox only tests these adjustments. The only clean test of the base portfolio is live from 1 Jan 2027.
- Settings already seen on the full history (noise band lookback 10/20, ATR band mult 0.4-0.6 and 30-min checks, expiry 9:35 / 11:30-12:30) are deliberately **left out**.

## Portfolio: netting, loss limits, risk caps, balancing

| id | adjustment | settings | nearby |
|---|---|---|---|
| P01 | Net same-minute opposite orders (cost saving only) (one futures account nets positions; only orders in the same minute (e.g. everyone flat at 3:55) actually save costs) | `{}` | n/a |
| P02 | Skip a new NQ trade if an opposite NQ position is open | `{'mode': 'skip'}` | n/a |
| P03 | Half size a new NQ trade if an opposite NQ position is open | `{'mode': 'half'}` | n/a |
| P04 | Exact-time daily loss limit -2R (realised) | `{'L': 2.0}` | {'L': 1.5}; {'L': 2.5} |
| P05 | Exact-time daily loss limit -1.5R (realised) | `{'L': 1.5}` | {'L': 1.0}; {'L': 2.0} |
| P06 | Exact-time daily loss limit -3R (realised) | `{'L': 3.0}` | {'L': 2.5}; {'L': 3.5} |
| P07 | Daily loss limit -2R counting open risk (worst case incl. open trades) | `{'L': 2.0, 'openrisk': True}` | {'L': 2.5, 'openrisk': True}; {'L': 3.0, 'openrisk': True} |
| P08 | Daily profit lock: no new trades after +4R realised | `{'P': 4.0}` | {'P': 3.0}; {'P': 5.0} |
| P09 | Total open-risk cap 2R (skip trades that would exceed it) | `{'cap': 2.0}` | {'cap': 1.5}; {'cap': 2.5} |
| P10 | Total open-risk cap 3R (skip) | `{'cap': 3.0}` | {'cap': 2.5}; {'cap': 3.5} |
| P11 | Total open-risk cap 2R (shrink new trade to fit, min 0.25) | `{'cap': 2.0, 'scale': True}` | {'cap': 1.5, 'scale': True}; {'cap': 2.5, 'scale': True} |
| P12 | Risk parity: weight = 1/stdev of last 6 months | `{'look': 6}` | {'look': 4}; {'look': 9} |
| P13 | Risk parity: weight = 1/stdev of last 12 months | `{'look': 12}` | {'look': 9}; {'look': 15} |
| P14 | Risk parity 6 months, weights capped 0.5-2 | `{'look': 6, 'lo': 0.5, 'hi': 2.0}` | {'look': 6, 'lo': 0.67, 'hi': 1.5}; {'look': 6, 'lo': 0.33, 'hi': 3.0} |
| P15 | Weight by trailing 12-month Sharpe (negative = 0) | `{'look': 12}` | {'look': 9}; {'look': 15} |
| P16 | Kill switch: strategy off while its last 12 months are negative | `{'look': 12}` | {'look': 9}; {'look': 15} |
| P17 | Kill switch: strategy off while its last 6 months are negative | `{'look': 6}` | {'look': 4}; {'look': 9} |
| P18 | Drawdown control: half size while portfolio is >15R below its peak | `{'dd': 15.0}` | {'dd': 10.0}; {'dd': 20.0} |
| P19 | Weekly loss limit -5R | `{'L': 5.0}` | {'L': 4.0}; {'L': 6.0} |
| P20 | Half size after 3 losing days in a row | `{'n': 3}` | {'n': 2}; {'n': 4} |
| P21 | Ensemble: 1.5x ATR band / noise band trades that agree with the day's QuantLab side | `{'boost': 1.5}` | {'boost': 1.25}; {'boost': 1.75} |
| P22 | Ensemble: skip ATR band / noise band trades against the day's QuantLab side | `{'mode': 'skip'}` | n/a |
| P23 | Ensemble: half ATR band / noise band trades against the day's QuantLab side | `{'mode': 'half'}` | n/a |
| P24 | Max 2 open same-direction NQ trades | `{'k': 2}` | {'k': 1}; {'k': 3} |
| P25 | Max 3 open NQ trades in any direction | `{'k': 3}` | {'k': 2}; {'k': 4} |
| P26 | Drop the ES expiry leg | `{'w': {'expiry_ES': 0.0}}` | n/a |
| P27 | Expiry leg 1.5x weight | `{'w': {'expiry': 1.5}}` | {'w': {'expiry': 1.25}}; {'w': {'expiry': 2.0}} |
| P28 | QuantLab 0.75x weight | `{'w': {'quantlab': 0.75}}` | {'w': {'quantlab': 0.6}}; {'w': {'quantlab': 0.9}} |
| P29 | Noise band 1.5x weight | `{'w': {'noiseband': 1.5}}` | {'w': {'noiseband': 1.25}}; {'w': {'noiseband': 1.75}} |
| P30 | ATR band 1.5x weight | `{'w': {'atrband': 1.5}}` | {'w': {'atrband': 1.25}}; {'w': {'atrband': 1.75}} |
| P31 | Skip the first Friday of each month (jobs report) for every strategy | `{'rule': 'first_friday'}` | n/a |
| P32 | Skip FOMC days entirely for every strategy | `{'rule': 'fomc'}` | n/a |
| P33 | Max 4 trades per day across the portfolio | `{'k': 4}` | {'k': 3}; {'k': 5} |
| P34 | Cooldown: no new trade for 30 min after any losing exit | `{'m': 30}` | {'m': 15}; {'m': 60} |
| P35 | Combo: loss limit -2R + open-risk cap 3R | `{'steps': [('losslimit', {'L': 2.0}), ('riskcap', {'cap': 3.0})]}` | {'steps': [('losslimit', {'L': 1.5}), ('riskcap', {'cap': 2.5})]}; {'steps': [('losslimit', {'L': 2.5}), ('riskcap', {'cap': 3.5})]} |
| P36 | Combo: loss limit -2R + risk parity 6m | `{'steps': [('parity', {'look': 6}), ('losslimit', {'L': 2.0})]}` | {'steps': [('parity', {'look': 4}), ('losslimit', {'L': 1.5})]}; {'steps': [('parity', {'look': 9}), ('losslimit', {'L': 2.5})]} |
| P37 | Priority trio: netting + risk parity 6m + loss limit -2R | `{'steps': [('parity', {'look': 6}), ('losslimit', {'L': 2.0}), ('netcost', {})]}` | {'steps': [('parity', {'look': 4}), ('losslimit', {'L': 1.5}), ('netcost', {})]}; {'steps': [('parity', {'look': 9}), ('losslimit', {'L': 2.5}), ('netcost', {})]} |

## Ensemble / calendar

| id | adjustment | settings | nearby |
|---|---|---|---|
| V01 | Noise band + ATR band: max 1 open same-direction trade between them | `{'k': 1}` | n/a |
| V02 | QuantLab: skip long trades on expiry Fridays (expiry is known in advance) | `{'mode': 'skip_long'}` | n/a |
| V03 | QuantLab: half size on expiry Fridays | `{'mode': 'half'}` | n/a |

## Risk level (reported only)

| id | adjustment | settings | nearby |
|---|---|---|---|
| S01 | Risk 0.5% per trade | `{'risk': 0.5}` | n/a |
| S02 | Risk 0.75% per trade | `{'risk': 0.75}` | n/a |
| S03 | Risk 1.0% per trade | `{'risk': 1.0}` | n/a |
| S04 | Risk 1.25% per trade | `{'risk': 1.25}` | n/a |

## QuantLab

| id | adjustment | settings | nearby |
|---|---|---|---|
| Q01 | Enter one 5-min bar later (9:40) | `{'delay': 1}` | {'delay': 2} |
| Q02 | Enter two 5-min bars later (9:45) | `{'delay': 2}` | {'delay': 1}; {'delay': 3} |
| Q03 | Pullback limit entry 0.25x first-candle range (by 10:00) | `{'pullback': 0.25}` | {'pullback': 0.15}; {'pullback': 0.35} |
| Q04 | Pullback limit entry 0.5x first-candle range (by 10:00) | `{'pullback': 0.5}` | {'pullback': 0.4}; {'pullback': 0.6} |
| Q05 | Concretum pullback: wait for one opposite 5-min bar, then enter (by 10:30) | `{'concretum': True}` | n/a |
| Q06 | ATR stop 0.075x daily ATR (was 0.10) | `{'stop_atr': 0.075}` | {'stop_atr': 0.06}; {'stop_atr': 0.09} |
| Q07 | ATR stop 0.125x daily ATR | `{'stop_atr': 0.125}` | {'stop_atr': 0.11}; {'stop_atr': 0.14} |
| Q08 | Chandelier set 2 / 2.5 / 3 | `{'chands': (2, 2.5, 3)}` | {'chands': (2, 2.5)}; {'chands': (2.5, 3)} |
| Q09 | Chandelier set 1.5 / 2 / 3 | `{'chands': (1.5, 2, 3)}` | {'chands': (1.25, 2, 3)}; {'chands': (1.75, 2, 3)} |
| Q10 | Chandelier set 2 / 3 / 4 | `{'chands': (2, 3, 4)}` | {'chands': (2, 3, 3.5)}; {'chands': (2, 3, 4.5)} |
| Q11 | Time exit 12:00 | `{'te': 720}` | {'te': 690}; {'te': 750} |
| Q12 | Time exit 14:00 | `{'te': 840}` | {'te': 810}; {'te': 870} |
| Q13 | Take half off at +2R | `{'partial': 2.0}` | {'partial': 1.5}; {'partial': 2.5} |
| Q14 | Take half off at +3R | `{'partial': 3.0}` | {'partial': 2.5}; {'partial': 3.5} |
| Q15 | Stop to breakeven after +1R | `{'be': 1.0}` | {'be': 0.75}; {'be': 1.25} |
| Q16 | Stop to breakeven after +2R | `{'be': 2.0}` | {'be': 1.5}; {'be': 2.5} |
| Q17 | Walk-forward lookback 3 months (was 6) | `{'_look': 3}` | {'_look': 2}; {'_look': 4} |
| Q18 | Walk-forward lookback 12 months | `{'_look': 12}` | {'_look': 9}; {'_look': 15} |
| Q19 | Walk-forward picks by Sharpe instead of total R | `{'_pick': 'sharpe'}` | n/a |
| Q20 | EMA exit needs 2 closes across | `{'confirm': 2}` | {'confirm': 3} |
| Q21 | Use a 10-minute first candle (9:30-9:40), enter 9:40 | `{'first': 10}` | n/a |
| Q22 | Candle stops only (3 variants) | `{'stops': ('candle',)}` | n/a |
| Q23 | ATR stops only (3 variants) | `{'stops': ('atr',)}` | n/a |
| Q24 | QuantLab skips FOMC days | `{'skip_fomc': True}` | n/a |
| Q25 | QuantLab flat 15:50 (was 15:55) | `{'flat': 950}` | {'flat': 945}; {'flat': 953} |

## Noise band

| id | adjustment | settings | nearby |
|---|---|---|---|
| N01 | Decisions every 15, 30 or 60 min (adds 15) | `{'freqs': (15, 30, 60)}` | n/a |
| N02 | Decisions every 30 min only | `{'freqs': (30,)}` | n/a |
| N03 | Band multipliers 0.8 / 1.0 / 1.5 | `{'mults': (0.8, 1.0, 1.5)}` | {'mults': (0.7, 1.0, 1.5)}; {'mults': (0.9, 1.0, 1.5)} |
| N04 | Band multipliers 1.0 / 1.25 / 1.5 | `{'mults': (1.0, 1.25, 1.5)}` | {'mults': (1.0, 1.15, 1.5)}; {'mults': (1.0, 1.35, 1.5)} |
| N05 | VWAP stop only | `{'stops': ('vwap',)}` | n/a |
| N06 | First decision 15 min earlier | `{'start': 585}` | n/a |
| N07 | No new entries after 14:00 (was 15:30) | `{'cutoff': 840}` | {'cutoff': 810}; {'cutoff': 870} |
| N08 | No new entries after 15:00 | `{'cutoff': 900}` | {'cutoff': 870}; {'cutoff': 915} |
| N09 | Need two decisions in a row outside the band | `{'confirm': True}` | n/a |
| N10 | Trailing stop 1.0 band-widths, checked every minute | `{'trail': 1.0}` | {'trail': 0.75}; {'trail': 1.25} |
| N11 | Trailing stop 2.0 band-widths | `{'trail': 2.0}` | {'trail': 1.5}; {'trail': 2.5} |
| N12 | Noise band flat 15:00 | `{'te': 900}` | {'te': 870}; {'te': 930} |
| N13 | Noise band flat 13:55 on FOMC days (like the others) | `{'fomc_flat': True}` | n/a |
| N14 | Noise band skips FOMC days | `{'skip_fomc': True}` | n/a |
| N15 | Walk-forward picks by Sharpe | `{'_pick': 'sharpe'}` | n/a |
| N16 | Walk-forward lookback 12 months | `{'_look': 12}` | {'_look': 9}; {'_look': 15} |
| N17 | Walk-forward lookback 3 months | `{'_look': 3}` | {'_look': 2}; {'_look': 4} |

## ATR band

| id | adjustment | settings | nearby |
|---|---|---|---|
| A01 | Trailing stop 0.5x daily ATR | `{'trail': 0.5}` | {'trail': 0.4}; {'trail': 0.6} |
| A02 | Trailing stop 1.0x daily ATR | `{'trail': 1.0}` | {'trail': 0.8}; {'trail': 1.2} |
| A03 | Stop to breakeven after +1R | `{'be': 1.0}` | {'be': 0.75}; {'be': 1.25} |
| A04 | Take half off at +1.5R | `{'partial': 1.5}` | {'partial': 1.25}; {'partial': 1.75} |
| A05 | Take half off at +2.5R | `{'partial': 2.5}` | {'partial': 2.0}; {'partial': 3.0} |
| A06 | One entry per day (no re-entry) | `{'maxent': 1}` | n/a |
| A07 | Max 2 entries per day | `{'maxent': 2}` | {'maxent': 3} |
| A08 | No new entries after 14:00 | `{'cutoff': 840}` | {'cutoff': 810}; {'cutoff': 870} |
| A09 | No new entries after 12:00 | `{'cutoff': 720}` | {'cutoff': 690}; {'cutoff': 750} |
| A10 | ATR band flat 15:00 | `{'te': 900}` | {'te': 870}; {'te': 930} |
| A11 | Stop halfway between open and band | `{'stopmode': 'mid'}` | n/a |
| A12 | Stop 0.25x ATR from entry | `{'stopmode': 'atr25'}` | n/a |
| A13 | Concretum pullback: wait for one opposite 1-min candle (max 15 min) | `{'concretum': True}` | n/a |
| A14 | Check every 10 minutes (was 15) | `{'step': 10}` | {'step': 5}; {'step': 12} |
| A15 | ATR band skips FOMC days | `{'skip_fomc': True}` | n/a |

## Expiry reversal

| id | adjustment | settings | nearby |
|---|---|---|---|
| E01 | Wider stop: first-minute range + 0.5x ATR | `{'stopk': 0.5}` | {'stopk': 0.4}; {'stopk': 0.6} |
| E02 | No stop (time exit only) | `{'nostop': True}` | n/a |
| E03 | Only after a gap up | `{'cond': True}` | n/a |
| E04 | Cover at 11:00 | `{'xm': 660}` | {'xm': 630}; {'xm': 690} |
| E05 | Quarterly expiries only | `{'quarterly': True}` | n/a |
| E06 | Skip expiries in an FOMC week | `{'skip_fomc_week': True}` | n/a |

## Clock changes (all strategies)

| id | adjustment | settings | nearby |
|---|---|---|---|
| C01 | Everything flat 15:50 (was 15:55) | `{'quantlab': {'flat': 950}, 'noiseband': {'flat': 950}, 'atrband': {'flat': 950}}` | {'quantlab': {'flat': 945}, 'noiseband': {'flat': 945}, 'atrband': {'flat': 945}}; {'quantlab': {'flat': 953}, 'noiseband': {'flat': 953}, 'atrband': {'flat': 953}} |
| C02 | No new entries after 15:00 anywhere | `{'noiseband': {'cutoff': 900}, 'atrband': {'cutoff': 900}}` | {'noiseband': {'cutoff': 870}, 'atrband': {'cutoff': 870}}; {'noiseband': {'cutoff': 915}, 'atrband': {'cutoff': 915}} |
