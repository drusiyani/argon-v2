# Round 2 results (test window Jul 2021 - Sep 2026)

Baseline Sharpe 1.157 (double costs 0.975). **Survivors: R01, R03**

| id | adjustment | dSharpe | dSharpe 2x cost | years better (vol-matched) | nearby ok | verdict |
|---|---|---|---|---|---|---|
| R01 | Risk parity: weight = 1/stdev of each strategy's last 12 months, average weight 1 | 0.128 | 0.166 | 4 | True | PASS |
| R03 | Risk parity 12 months, weights capped 0.5-2 | 0.118 | 0.136 | 4 | True | PASS |
| E02 | Everything flat 15:45 instead of 15:55 (avoids the 3:50pm order-flow burst) | 0.101 | 0.076 | 4 | False | fail |
| R02 | Risk parity, 6 months | 0.054 | 0.107 | 4 | True | fail |
| G01 | QuantLab skips days whose overnight gap is bigger than 1x daily ATR | 0.045 | 0.062 | 5 | False | fail |
| S02 | Add the ATR band on ES | 0.022 | -0.003 | 4 | False | fail |
| W02 | Noise band trades its top 2 variants at half size each | 0.022 | -0.012 | 6 | False | fail |
| R05 | Equal risk per strategy per month | 0.019 | 0.035 | 2 | False | fail |
| P01 | Noise band + ATR band: if one is already open in the same direction, the later one enters at half size | 0.012 | 0.002 | 4 | False | fail |
| X02 | Expiry enters with a limit at the 9:31 open | -0.001 | -0.001 | 3 | False | fail |
| E01 | ATR band re-picks its exit monthly: no trail / 0.5x ATR trail / 1x ATR trail | -0.023 | -0.024 | 1 | False | fail |
| S01 | Add the noise band on ES (walk-forward, same variants) | -0.046 | -0.118 | 2 | False | fail |
| C01 | Skip days next to market holidays and 20 Dec - 2 Jan | -0.08 | -0.079 | 3 | False | fail |
| R04 | Volatility target for the whole book | -0.103 | -0.073 | 3 | False | fail |
| W01 | QuantLab trades its top 2 variants at half size each | -0.133 | -0.186 | 1 | False | fail |
| X01 | QuantLab enters with a limit at the 9:35 open | -0.142 | -0.153 | 2 | False | fail |
| W03 | Re-pick looks back 12 months; if the best variant did not break even, use the default | -0.198 | -0.199 | 1 | False | fail |
