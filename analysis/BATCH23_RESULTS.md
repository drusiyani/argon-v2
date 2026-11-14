# Batch 23 results (14 Nov 2026): by the rule fixed in advance, the model's skill "does not carry"; the detail is mixed

Pre-registration: `BATCH23_PREREG.md` (committed before the run). Code: `batch23_dump.py`, `batch23.py`. Raw: `batch23.json`.
Train: 4,417 real-book trades, 2018–2026, one fit. Test: 3,827 scenario trades before 2018, of which 1,491 are QuantLab
trades on days QuantLab was never in the real book.

## Verdict by the pre-registered readings: "does not carry"
| Check | Result |
|---|---|
| (a) top minus bottom above zero in 2010–13 AND 2014–17, all test trades | yes (+0.05R, +0.31R) |
| (b) the same for never-seen QuantLab trades | **no** (−0.06R in 2010–13, +0.40R in 2014–17) |
| (c) skip-only beats the scenario package over 2010–17 | yes |
| (d) under 5% of random rules beat skip-only | yes (0.4%) |

(b) failed, and the rule said that if (a) or (b) fails the reading is "does not carry". That stands.

## The detail
Average R per trade in the scenario, bottom third / middle / top third (t-statistic of top minus bottom):

| | 2010–13 | 2014–17 |
|---|---|---|
| All test trades | −0.02 / +0.01 / +0.03 (t 0.5) | −0.06 / +0.12 / +0.25 (t 3.4) |
| Never-seen QuantLab | +0.02 / +0.04 / −0.04 (t −0.3) | −0.13 / +0.31 / +0.27 (t 2.1) |
| Noise band + ATR band | −0.03 / +0.02 / +0.04 (t 1.1) | −0.07 / −0.07 / +0.21 (t 3.4) |

- In 2010–13 there was almost no edge to rank (batch 22: +0R to +26R a year before friction), and the model found nothing.
- In 2014–17, when the edge existed, a model that had only seen 2018–26 separated good from bad trades clearly, including
  on QuantLab trades no scan or model had ever touched.
- The answer does not hinge on the scenario: on friction-free outcomes the gaps are +0.07R (t 0.7) and +0.33R (t 3.6).
- **For QuantLab the model spots the worst trades, not the best.** The top third did no better than the middle third
  (+0.16R against +0.21R over 2010–17). Skipping is supported; pressing is not.

## Package over 2010–17 at today's friction (scenario)
| | Return a year | Sortino | Worst drop | Chance of a drop worse than −35% |
|---|---|---|---|---|
| Fixed size | +36.1% | 2.62 | −30.4% | 8.9% |
| Skip-only | +42.2% | 3.16 | −22.5% | 3.2% |
| Skip-and-press | +50.2% | 3.38 | −27.3% | 10.3% |
| Core only | +17.8% | 1.66 | −17.1% | 0.0% |

Random rules beating skip-only's return: 21 of 5,000. Beating skip-and-press's: 10 of 5,000.

## What it means
- The model is not a general skill. It works when the momentum edge is there and does nothing when it is not. If 2027 is an
  edge-less year like 2010–13, the model will not rescue the rules; skip-only would still cut exposure by about a third.
- Skip-only is supported again, and with a much shallower worst drop than fixed size in the scenario (−22.5% against −30.4%).
- Skip-and-press is not supported by the unseen QuantLab trades.
- Honest notes from the pre-registration apply: a backward test, scenario outcomes, and the noise band / ATR band trades
  were not clean. This sample is now used and cannot serve as an unseen test again.
