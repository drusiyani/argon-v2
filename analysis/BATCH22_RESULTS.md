# Batch 22 results (14 Nov 2026): the "no edge before 2018" claim is withdrawn. It was friction

Pre-registration: `BATCH22_PREREG.md` (committed before the run). Code: `batch22.py`. Raw: `batch22_*.json`.

## Part 1 — The same trades with no friction
The three momentum rules' picked trades (before the cost rule), total R per year.

| Year | Nasdaq: real, after all friction | Nasdaq: friction-free | S&P: real | S&P: friction-free |
|---|---|---|---|---|
| 2010 (Jul–Dec) | −14 | +0 | −21 | +1 |
| 2011 | −136 | +5 | −182 | +37 |
| 2012 | −126 | +19 | −260 | −15 |
| 2013 | −126 | +26 | −255 | +1 |
| 2014 | −90 | +45 | −178 | +32 |
| 2015 | −24 | +78 | −121 | +42 |
| 2016 | −54 | +53 | −181 | +20 |
| 2017 | −49 | +66 | −229 | −2 |
| 2018 | +66 | +124 | −81 | +70 |
| 2019 | +48 | +103 | −107 | +81 |
| 2020 | +20 | +48 | −116 | +4 |
| 2021 (Jul–Dec) | +31 | +52 | −27 | +26 |
| 2022 | +63 | +83 | −1 | +61 |
| 2023 | +71 | +96 | −53 | +50 |
| 2024 | +75 | +99 | −121 | −14 |
| 2025 | +49 | +68 | −9 | +64 |
| 2026 (to 12 Nov) | +12 | +22 | −59 | +0 |

Matching: 99.9% of Nasdaq trades and 99.7% of S&P trades were matched to their friction-free twin.

**Readings fixed in advance:**
- **Nasdaq: positive in 8 of 8 years 2010–17 (17 of 17 overall). The claim "no edge in 2010–17, even before costs" is
  WITHDRAWN.** The "before costs" figures Claude quoted since batch 11 still contained tick slippage. Friction took about
  140–150R a year in 2011–13 and about 100–115R in 2015–17, against 20–25R a year in 2022–25 and 10R in 2026.
  The honest picture: no edge in 2010–11, a small one in 2012–13, then 45–78R a year in 2014–17, which is the same
  range as 2025. The "break in 2018" is the year friction fell below the edge, as the index and volatility rose.
- **S&P: positive in 14 of 17 years. The rules' failure on the S&P is mainly friction.** The edge is there but about half
  the Nasdaq's size, and S&P friction is still 60–75R a year in 2025–26, so it is not tradable.

QuantLab alone, friction-free: 2011 +1, 2012 +5, 2013 +28, 2014 +51, 2015 +62, 2016 +63, 2017 +58, 2018 +55, 2019 +113,
2020 +17, 2021 (half) +36, 2022 +50, 2023 +59, 2024 +80, 2025 +47, 2026 +17.

## Part 2 — Scenario: the same history at today's relative friction (a scenario, NOT history)
Fixed size, no model, rules weight 0.5.
Each cell: return a year / Sharpe / worst drop / bootstrap chance of a drop worse than −35%.

| | 2010–20 | 2021–26 |
|---|---|---|
| Package, real history | +21.6% / 1.05 / −23.5% / 7.4% | +56.4% / 1.61 / −19.4% / 1.0% |
| Package, today's friction | +48.7% / 1.60 / −30.4% / 7.5% | +62.8% / 1.74 / −18.9% / 0.4% |
| Core only | +20.7% / 1.26 / −17.8% / 1.0% | +18.7% / 0.91 / −25.8% / 10.8% |

Sub-periods (return a year / worst drop): 2010–17 real +10.6% / −23.5%, scenario +36.1% / −30.4%, core only +17.8% / −17.1%.
2018–20 real +53.9% / −20.4%, scenario +85.7% / −20.0%. 2021–25 real +64.2%, scenario +72.0%. 2026 real +19.1%, scenario +19.2%.

Rules' R by year in the scenario: 2010 +4, 2011 −17, 2012 +12, 2013 +7, 2014 +39, 2015 +74, 2016 +36, 2017 +78, 2018 +118,
2019 +88, 2020 +28, 2021 (half) +42, 2022 +78, 2023 +79, 2024 +90, 2025 +56, 2026 +16.

## What this changes
1. **The edge is about 13 years old, not 9**, and it showed up in calm years (2014–17) as well as wild ones. That is better
   evidence that it is a lasting feature of the Nasdaq.
2. **Why "every filter splits the decades":** in the high-friction years the average trade lost money, so anything that
   removed trades helped. In the low-friction years the average trade made money, so removing trades hurt. Many "split"
   verdicts in batches 4–12 were about friction, not about the idea.
3. **"Fitted to the Nasdaq" was too strong.** The same rules have an edge on the S&P before friction. The Nasdaq future is
   simply the one where the tick is small against the index's price and movement.
4. **2026 is still a real worry.** At today's friction it is the weakest full year since 2013 (+16R), in the same range as
   the early years when the edge was close to absent (−17R to +12R).
5. **Risk reads worse, not better.** At today's index level the cost rule no longer keeps QuantLab out in a year with no
   edge. In the scenario the worst drop is −30.4% (2010–17), against −23.5% in real history.
6. The council (14 Nov) was given the withdrawn claim as a fact. Its "nine winning years after eight with nothing" reading
   should be discounted accordingly; its points on costs, tails and 2026 stand.

## Limits
The scenario is hypothetical. When friction was high, nobody could trade this edge away; at today's friction anyone can, so
the scenario probably overstates what the early years would really have paid. It is not used to pass a mark or to argue
for more size.
