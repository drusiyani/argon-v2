# Argon v2: round 2 pre-registered adjustments + the 2010-2020 lockbox

17 adjustments, committed **before any round-2 test code exists**. Reviewed by a 5-member council (statistician, risk manager, execution trader, sceptic, methodologist).

**Baseline:** The final v2 book (Amendment 3): QuantLab (NQ, walk-forward, skips FOMC days) + noise band (NQ) + ATR band (NQ) + expiry reversal (NQ + ES), 1R per trade each, 0.75% risk, no daily loss limit.

## Rules (fixed now)

- Test window: Jul 2021 - Sep 2026. Lockbox: Jan 2011 - Dec 2020, opened ONCE, for the survivors AND the base book (B0), in a single run whose results are written to a file before anyone reads them.
- Pass marks (all must hold): Sharpe at least +0.10 over the baseline; better than the baseline in at least 4 of the 6 years, with each year compared at the SAME volatility (the adjustment's monthly series is rescaled to the baseline's standard deviation first: this fixes round 1's risk-parity flaw); at least +0.05 better at double costs; every nearby setting at least +0.05 better.
- Lockbox pass: Sharpe at least +0.03 over the baseline at normal costs AND better at double costs. Fail = out, no retries.
- B0 (the base book itself on 2011-2020): passes if Sharpe >= 0.4, Sharpe > 0 at double costs, and positive in at least 6 of 10 years. IF B0 FAILS, NOTHING CHANGES: the book still goes live on 1 Jan 2027 and the write-up says so.
- Costs are real tick-based costs (NQ 0.75, ES 0.5 points a round trip, same slippage rules). NQ was ~2,000 in 2010 vs ~20,000 now, so costs in R were 5-10x heavier then. Results at real costs are what count; a version with costs scaled to the price level is reported for information only and cannot rescue a fail.
- Data rule (both windows): skip any day missing more than 10% of its 9:30-16:00 minutes (checked on timestamps only: removes 0 lockbox days); half days (<=300 session minutes) are skipped by the loader as always (78 in the lockbox).
- FOMC days 2010-2020 from research/calendar_hist.py (Fed historical pages). Before Mar 2013 be flat by 12:25pm; 3 Mar 2020 by 9:55am; otherwise 1:55pm.
- Walk-forward strategies in the lockbox re-pick only from earlier lockbox months (warm-up Jun-Dec 2010), never from 2021+.
- Holiday = a weekday with no session or a session of <=300 minutes (derived from the data; holidays are known in advance in real life).
- Every "nearby" setting below is fixed now. Trials this round: 17 adjustments + 32 nearby settings, each also at double costs.

## Adjustments

| id | adjustment | settings | nearby | note |
|---|---|---|---|---|
| R01 | Risk parity: weight = 1/stdev of each strategy's last 12 months, average weight 1 | `{'rule': 'parity', 'look': 12}` | {'look': 9}; {'look': 15} |  |
| R02 | Risk parity, 6 months | `{'rule': 'parity', 'look': 6}` | {'look': 4}; {'look': 9} |  |
| R03 | Risk parity 12 months, weights capped 0.5-2 | `{'rule': 'parity', 'look': 12, 'lo': 0.5, 'hi': 2.0}` | {'look': 12, 'lo': 0.67, 'hi': 1.5}; {'look': 12, 'lo': 0.33, 'hi': 3.0} |  |
| R04 | Volatility target for the whole book | `{'rule': 'voltarget', 'look': 6, 'cap': 1.5, 'floor': 0.5}` | {'look': 3, 'cap': 1.5, 'floor': 0.5}; {'look': 12, 'cap': 1.5, 'floor': 0.5} | scale = (expanding median of past monthly stdev, min 12 months) / (stdev of last `look` months), capped at 1.5x and floored at 0.5x |
| R05 | Equal risk per strategy per month | `{'rule': 'eqcount', 'look': 6, 'lo': 0.25, 'hi': 4.0}` | {'look': 3, 'lo': 0.25, 'hi': 4.0}; {'look': 12, 'lo': 0.25, 'hi': 4.0} | each strategy scaled so its trailing trades-per-month matches the book average, capped 0.25-4x |
| S01 | Add the noise band on ES (walk-forward, same variants) | `{'strat': 'noiseband', 'sym': 'ES', 'w': 1.0}` | {'w': 0.75}; {'w': 1.25} |  |
| S02 | Add the ATR band on ES | `{'strat': 'atrband', 'sym': 'ES', 'w': 1.0}` | {'w': 0.75}; {'w': 1.25} |  |
| X01 | QuantLab enters with a limit at the 9:35 open | `{'strat': 'quantlab', 'limit_ticks': 0}` | {'limit_ticks': -1}; {'limit_ticks': 1} | fills only if the 9:35 minute trades 1 full tick through the limit; otherwise market at the 9:36 open + 2 ticks. Worst case assumed inside the minute. |
| X02 | Expiry enters with a limit at the 9:31 open | `{'strat': 'expiry', 'limit_ticks': 0}` | {'limit_ticks': -1}; {'limit_ticks': 1} | same fill rule; fallback market at the 9:32 open + 1 tick |
| W01 | QuantLab trades its top 2 variants at half size each | `{'strat': 'quantlab', 'topk': 2}` | {'topk': 3} |  |
| W02 | Noise band trades its top 2 variants at half size each | `{'strat': 'noiseband', 'topk': 2}` | {'topk': 3} |  |
| W03 | Re-pick looks back 12 months; if the best variant did not break even, use the default | `{'strat': 'both', 'look': 12, 'fallback': True}` | {'look': 9, 'fallback': True}; {'look': 15, 'fallback': True} | defaults: QuantLab candle stop + EMA exit; noise band 30 min, 1.0x band, VWAP stop |
| P01 | Noise band + ATR band: if one is already open in the same direction, the later one enters at half size | `{'rule': 'pairhalf', 'size': 0.5}` | {'size': 0.33}; {'size': 0.67} |  |
| C01 | Skip days next to market holidays and 20 Dec - 2 Jan | `{'rule': 'calendar', 'start': '12-20', 'end': '01-02'}` | {'start': '12-22', 'end': '01-02'}; {'start': '12-15', 'end': '01-03'} |  |
| G01 | QuantLab skips days whose overnight gap is bigger than 1x daily ATR | `{'strat': 'quantlab', 'gap_atr': 1.0}` | {'gap_atr': 0.75}; {'gap_atr': 1.25} | gap = 9:30 open vs previous 16:00 close; ATR = 14 previous sessions |
| E01 | ATR band re-picks its exit monthly: no trail / 0.5x ATR trail / 1x ATR trail | `{'strat': 'atrband', 'exitpick': (None, 0.5, 1.0), 'look': 6}` | {'look': 3}; {'look': 12} |  |
| E02 | Everything flat 15:45 instead of 15:55 (avoids the 3:50pm order-flow burst) | `{'flat': 945}` | {'flat': 940}; {'flat': 950} |  |

## Dropped after review

- Early-close days (already skipped by the loader)
- QuantLab half size on big-gap days (near-copy of a round-1 failure)
- Daily loss limits, pullback/delayed entries, QuantLab filters, other markets (failed in round 1 or ruled out)

## Pre-commit checks (timestamps and counts only, no prices)

- Lockbox: 22 files, 2010-06-07 to 2020-12-31, sha256 in data/lockbox2010/MANIFEST.json, no duplicate minutes, symbol correct.
- 2,711 sessions per market; 0 days fail the 10% rule; 78 half days; first bar 9:30 New York on every session (DST correct); 4 rolls a year.
- 48 full-closure weekday holidays found (incl. Hurricane Sandy, 29 Oct 2012).
- FOMC: the engine calendar only covered 2021+, which would have silently broken the FOMC rules in the lockbox. Fixed: 88 decision days in research/calendar_hist.py.
- Nothing outside a lockbox run reads data/lockbox2010/.
