# Adjustment test results (Jul 2021 - Dec 2024, lockbox closed)

Baseline Sharpe 1.412 (double costs 1.154), 240.49R. Tested 109 of 109. **Survivors: Q24**

| id | adjustment | dSharpe | dSharpe 2x cost | years better | nearby ok | verdict |
|---|---|---|---|---|---|---|
| P13 | Risk parity: weight = 1/stdev of last 12 months | 0.256 | 0.288 | 0 | True | fail |
| P14 | Risk parity 6 months, weights capped 0.5-2 | 0.16 | 0.18 | 0 | True | fail |
| Q20 | EMA exit needs 2 closes across | 0.12 | 0.122 | 2 | False | fail |
| N03 | Band multipliers 0.8 / 1.0 / 1.5 | 0.108 | 0.131 | 2 | True | fail |
| Q24 | QuantLab skips FOMC days | 0.103 | 0.108 | 3 | True | PASS |
| Q10 | Chandelier set 2 / 3 / 4 | 0.102 | 0.116 | 2 | False | fail |
| N11 | Trailing stop 2.0 band-widths | 0.082 | 0.081 | 3 | False | fail |
| P32 | Skip FOMC days entirely for every strategy | 0.072 | 0.074 | 3 | True | fail |
| P28 | QuantLab 0.75x weight | 0.069 | 0.074 | 0 | False | fail |
| P12 | Risk parity: weight = 1/stdev of last 6 months | 0.06 | 0.104 | 0 | False | fail |
| Q07 | ATR stop 0.125x daily ATR | 0.056 | 0.025 | 2 | False | fail |
| P30 | ATR band 1.5x weight | 0.055 | 0.058 | 4 | False | fail |
| P01 | Net same-minute opposite orders (cost saving only) | 0.042 | 0.086 | 4 | True | fail |
| P02 | Skip a new NQ trade if an opposite NQ position is open | 0.035 | 0.04 | 3 | True | fail |
| E04 | Cover at 11:00 | 0.034 | 0.029 | 2 | False | fail |
| V02 | QuantLab: skip long trades on expiry Fridays (expiry is known in advance) | 0.03 | 0.035 | 3 | True | fail |
| A14 | Check every 10 minutes (was 15) | 0.028 | 0.029 | 3 | True | fail |
| P08 | Daily profit lock: no new trades after +4R realised | 0.025 | 0.025 | 3 | False | fail |
| P29 | Noise band 1.5x weight | 0.025 | 0.028 | 4 | False | fail |
| P27 | Expiry leg 1.5x weight | 0.024 | 0.026 | 4 | False | fail |
| A12 | Stop 0.25x ATR from entry | 0.021 | 0.021 | 3 | True | fail |
| P03 | Half size a new NQ trade if an opposite NQ position is open | 0.018 | 0.021 | 3 | True | fail |
| Q09 | Chandelier set 1.5 / 2 / 3 | 0.018 | 0.019 | 1 | False | fail |
| N10 | Trailing stop 1.0 band-widths, checked every minute | 0.018 | -0.005 | 1 | False | fail |
| A13 | Concretum pullback: wait for one opposite 1-min candle (max 15 min) | 0.017 | 0.016 | 3 | True | fail |
| E06 | Skip expiries in an FOMC week | 0.017 | 0.018 | 3 | True | fail |
| N04 | Band multipliers 1.0 / 1.25 / 1.5 | 0.016 | 0.033 | 1 | False | fail |
| N05 | VWAP stop only | 0.013 | 0.014 | 3 | True | fail |
| N16 | Walk-forward lookback 12 months | 0.012 | 0.014 | 2 | False | fail |
| A11 | Stop halfway between open and band | 0.01 | 0.014 | 3 | True | fail |
| A15 | ATR band skips FOMC days | 0.008 | 0.008 | 3 | True | fail |
| P31 | Skip the first Friday of each month (jobs report) for every strategy | 0.007 | 0.024 | 2 | True | fail |
| A03 | Stop to breakeven after +1R | 0.007 | 0.007 | 2 | False | fail |
| P21 | Ensemble: 1.5x ATR band / noise band trades that agree with the day's QuantLab side | 0.006 | 0.01 | 4 | False | fail |
| A04 | Take half off at +1.5R | 0.003 | 0.002 | 2 | False | fail |
| Q25 | QuantLab flat 15:50 (was 15:55) | 0.002 | 0.002 | 1 | False | fail |
| A02 | Trailing stop 1.0x daily ATR | 0.001 | 0.001 | 2 | False | fail |
| A01 | Trailing stop 0.5x daily ATR | 0.0 | -0.002 | 2 | False | fail |
| A05 | Take half off at +2.5R | 0.0 | 0.0 | 2 | False | fail |
| A07 | Max 2 entries per day | 0.0 | 0.0 | 0 | False | fail |
| P25 | Max 3 open NQ trades in any direction | -0.004 | -0.005 | 1 | False | fail |
| V03 | QuantLab: half size on expiry Fridays | -0.005 | -0.005 | 1 | True | fail |
| N02 | Decisions every 30 min only | -0.006 | 0.005 | 2 | True | fail |
| N17 | Walk-forward lookback 3 months | -0.007 | 0.007 | 2 | False | fail |
| A06 | One entry per day (no re-entry) | -0.015 | -0.013 | 1 | True | fail |
| P10 | Total open-risk cap 3R (skip) | -0.017 | -0.02 | 1 | False | fail |
| Q12 | Time exit 14:00 | -0.018 | -0.011 | 2 | False | fail |
| N08 | No new entries after 15:00 | -0.023 | -0.019 | 1 | False | fail |
| C02 | No new entries after 15:00 anywhere | -0.025 | -0.02 | 1 | False | fail |
| P26 | Drop the ES expiry leg | -0.026 | -0.026 | 0 | True | fail |
| N14 | Noise band skips FOMC days | -0.026 | -0.029 | 1 | True | fail |
| N06 | First decision 15 min earlier | -0.028 | -0.063 | 2 | True | fail |
| A08 | No new entries after 14:00 | -0.03 | -0.027 | 0 | False | fail |
| E02 | No stop (time exit only) | -0.03 | -0.031 | 2 | True | fail |
| E01 | Wider stop: first-minute range + 0.5x ATR | -0.031 | -0.031 | 0 | False | fail |
| C01 | Everything flat 15:50 (was 15:55) | -0.034 | -0.019 | 1 | False | fail |
| N01 | Decisions every 15, 30 or 60 min (adds 15) | -0.038 | -0.075 | 1 | True | fail |
| P34 | Cooldown: no new trade for 30 min after any losing exit | -0.039 | -0.036 | 1 | False | fail |
| N15 | Walk-forward picks by Sharpe | -0.044 | -0.062 | 1 | True | fail |
| E03 | Only after a gap up | -0.044 | -0.044 | 0 | True | fail |
| Q19 | Walk-forward picks by Sharpe instead of total R | -0.049 | -0.087 | 1 | True | fail |
| E05 | Quarterly expiries only | -0.049 | -0.049 | 0 | True | fail |
| N07 | No new entries after 14:00 (was 15:30) | -0.057 | -0.057 | 1 | False | fail |
| N13 | Noise band flat 13:55 on FOMC days (like the others) | -0.057 | -0.051 | 0 | True | fail |
| V01 | Noise band + ATR band: max 1 open same-direction trade between them | -0.06 | -0.067 | 1 | True | fail |
| P33 | Max 4 trades per day across the portfolio | -0.064 | -0.063 | 0 | False | fail |
| Q08 | Chandelier set 2 / 2.5 / 3 | -0.067 | -0.07 | 1 | False | fail |
| P17 | Kill switch: strategy off while its last 6 months are negative | -0.074 | -0.28 | 1 | False | fail |
| P06 | Exact-time daily loss limit -3R (realised) | -0.083 | -0.077 | 0 | False | fail |
| P23 | Ensemble: half ATR band / noise band trades against the day's QuantLab side | -0.085 | -0.083 | 0 | True | fail |
| N12 | Noise band flat 15:00 | -0.085 | -0.063 | 2 | False | fail |
| A10 | ATR band flat 15:00 | -0.085 | -0.087 | 1 | False | fail |
| A09 | No new entries after 12:00 | -0.089 | -0.081 | 1 | False | fail |
| P04 | Exact-time daily loss limit -2R (realised) | -0.108 | -0.107 | 1 | False | fail |
| P24 | Max 2 open same-direction NQ trades | -0.109 | -0.115 | 0 | False | fail |
| N09 | Need two decisions in a row outside the band | -0.109 | -0.119 | 2 | True | fail |
| P37 | Priority trio: netting + risk parity 6m + loss limit -2R | -0.113 | -0.017 | 0 | False | fail |
| P05 | Exact-time daily loss limit -1.5R (realised) | -0.121 | -0.106 | 1 | False | fail |
| P35 | Combo: loss limit -2R + open-risk cap 3R | -0.125 | -0.128 | 0 | False | fail |
| P09 | Total open-risk cap 2R (skip trades that would exceed it) | -0.128 | -0.131 | 0 | False | fail |
| P11 | Total open-risk cap 2R (shrink new trade to fit, min 0.25) | -0.128 | -0.131 | 0 | False | fail |
| P20 | Half size after 3 losing days in a row | -0.129 | -0.256 | 0 | False | fail |
| Q11 | Time exit 12:00 | -0.133 | -0.148 | 1 | False | fail |
| P36 | Combo: loss limit -2R + risk parity 6m | -0.139 | -0.069 | 0 | False | fail |
| P16 | Kill switch: strategy off while its last 12 months are negative | -0.147 | -0.347 | 0 | False | fail |
| Q23 | ATR stops only (3 variants) | -0.156 | -0.152 | 0 | True | fail |
| P15 | Weight by trailing 12-month Sharpe (negative = 0) | -0.178 | -0.162 | 0 | False | fail |
| P18 | Drawdown control: half size while portfolio is >15R below its peak | -0.182 | -0.039 | 0 | False | fail |
| P19 | Weekly loss limit -5R | -0.188 | -0.162 | 1 | False | fail |
| P22 | Ensemble: skip ATR band / noise band trades against the day's QuantLab side | -0.19 | -0.178 | 0 | True | fail |
| Q16 | Stop to breakeven after +2R | -0.209 | -0.255 | 1 | False | fail |
| Q06 | ATR stop 0.075x daily ATR (was 0.10) | -0.212 | -0.239 | 1 | False | fail |
| Q22 | Candle stops only (3 variants) | -0.225 | -0.272 | 0 | True | fail |
| Q15 | Stop to breakeven after +1R | -0.242 | -0.304 | 1 | False | fail |
| Q21 | Use a 10-minute first candle (9:30-9:40), enter 9:40 | -0.247 | -0.224 | 1 | True | fail |
| Q14 | Take half off at +3R | -0.257 | -0.232 | 0 | False | fail |
| Q17 | Walk-forward lookback 3 months (was 6) | -0.295 | -0.255 | 0 | False | fail |
| Q13 | Take half off at +2R | -0.32 | -0.411 | 0 | False | fail |
| Q02 | Enter two 5-min bars later (9:45) | -0.327 | -0.438 | 1 | False | fail |
| P07 | Daily loss limit -2R counting open risk (worst case incl. open trades) | -0.412 | -0.405 | 0 | False | fail |
| Q18 | Walk-forward lookback 12 months | -0.501 | -0.393 | 0 | False | fail |
| Q01 | Enter one 5-min bar later (9:40) | -0.612 | -0.599 | 0 | False | fail |
| Q04 | Pullback limit entry 0.5x first-candle range (by 10:00) | -0.812 | -0.845 | 0 | False | fail |
| Q03 | Pullback limit entry 0.25x first-candle range (by 10:00) | -0.858 | -0.901 | 0 | False | fail |
| Q05 | Concretum pullback: wait for one opposite 5-min bar, then enter (by 10:30) | -0.859 | -0.902 | 0 | True | fail |

## Risk levels (reported, not pass/fail)

| risk | a year | worst drop | halving chance |
|---|---|---|---|
| 0.5% | 36.6% | -15.0% | 0.0% |
| 0.75% | 56.3% | -22.4% | 0.6% |
| 1.0% | 76.5% | -29.5% | 3.2% |
| 1.25% | 96.9% | -36.4% | 10.9% |
