# Batch 31 results: Gemini T13 (19 Nov 2026). Both testable ideas fail.

| | 2021–26 | 2010–20 | Strict vs G3 | Luck (of 5,000) |
|---|---|---|---|---|
| G3 | +60.2% / 3.41 / −18.4% / 0.7% | +29.1% / 2.36 / −21.2% / 0.9% | — | — |
| V1 pre-settlement overnight leg | +59.9% / 3.37 / −19.2% / 0.7% | +29.6% / 2.38 / −21.6% / 1.3% | no | 99 |
| V2 size-scaled ridge penalty | +57.0% / 3.25 / −18.9% / 0.6% | +27.7% / 2.26 / −21.2% / 1.7% | no | 0 |

- **V1:** the expiry-night effect is real in 2010–20 (+11.5 bp vs +2.4 bp on other Friday nights, matching the paper's
  2003–2021 sample) and **gone in 2021–26** (−2.6 bp vs −0.5 bp), consistent with 0DTE and PM-settled options diluting
  the AM settlement. The fade half of the idea was already in the book (the expiry rule).
- **V2:** a penalty that grows with the training set made G3 worse in both eras. The fixed penalty stays.

## Triage of the rest of T13 (not tested, with reasons)
- Answered a different list of "Ideas 1–10" (60/40 rebalancing, dash-for-cash, COT, VVIX, fixed-share, LETF…), not
  the T13 brief; no ranked odds, no do-nothing assessment, no view on 0.5% vs 0.625%.
- **Cost "distortion" claim rejected:** a fixed point cost is NOT a bias. Tick size and per-contract fees were the
  same in points in 2010, so friction really was ~10× larger relative to price. Batch 22 showed this is why the rules
  lost money before 2018. Scaling costs to price would flatter 2010–20 falsely.
- Idea 12 (0DTE hedge unwind): needs OPRA options data, post-2022 only. Cannot pass both eras; at most a live log.
- Idea 14 (30-min noise band + VWAP): already the book's noise-band rule.
- Ideas 1, 7, 16 (month-end / PreTOM / calendar density): mostly single-stock and bond effects; index turn-of-month
  is reported dead by Gemini's own sources; roll week already tested (batch 29).
- Idea 13 (multi-horizon vol overlay): a variant of the core's VXN sizing and H3 (failed batch 9). Low priority.
- Idea 15 (net Fed liquidity, auctions): a monthly 4-month-lagged signal from a non-peer-reviewed post; core-level,
  slow, small sample. Not tested.
- Race 1 scoring advice (rank correlation and AUC rather than binned Brier scores; recalibrate the AIs out of fold;
  leave-two-out P&L): sound and consistent with T12. **Adopt for the desk evaluation.**
- Many 2026 citations (Nov 2026 working papers, CFTC release 9316-26, Databento's $199/month price, arXiv 2608.03703)
  are after our verification ability and are treated as unverified.

Running total about 296 trials. No change to the book.
