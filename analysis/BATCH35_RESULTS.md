# Batch 35 results (23 Nov 2026): minimum stop for Opening Drive. **Rejected: nothing changes.**

Every variant lowered the book's Sharpe in BOTH eras, so none passes the pre-registered bar (+0.05 in both).

| Variant | Sharpe 2021-26 | Sharpe 2011-20 | Opening Drive total R 2021-26 / 2011-20 |
|---|---|---|---|
| current | **1.221** | **0.104** | 195 / 40 |
| widen k=0.02 | 1.214 | 0.099 | 192 / 39 |
| widen k=0.04 | 1.195 | 0.078 | 186 / 32 |
| widen k=0.06 | 1.122 | 0.054 | 159 / 25 |
| skip k=0.02 | 1.131 | 0.102 | 166 / 40 |
| skip k=0.04 | 0.987 | 0.093 | 113 / 37 |
| skip k=0.06 | 1.212 | 0.010 | 169 / 11 |

Reading: the tight-stop days are a big part of where Opening Drive makes its money. A close stop means a small loss when
wrong and a large multiple of R when right (23 Nov is the losing half of that trade-off). Seven more trials are added to
the project's count. Files: `batch35_databento.json`, `batch35_lockbox2010.json`.
