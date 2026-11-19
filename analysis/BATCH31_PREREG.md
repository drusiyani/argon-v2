# Batch 31 pre-registration: Gemini T13 (19 Nov 2026)

Written and committed before any Batch 31 code ran. Gemini's T13 report proposed 16 ideas. Only two are testable on
BOTH eras with data we already hold and are not already in the book or already failed. Everything else is triaged in
BATCH31_RESULTS.md. Reference: G3 (+60.2% / 3.41 / −18.4% / 0.7% | +29.1% / 2.36 / −21.2% / 0.9%).
Noise floor (batch 29 jitter test): gains under 3 points (2021–26) or 1.5 points (2010–20) are reported as noise.

**V1. Pre-settlement overnight leg (Gemini Idea 11, after Baltussen, Terstegge & Whelan, "the derivative payoff
bias").** On every monthly-expiry Friday (Friday falling on the 15th–21st), add a long Nasdaq position of
0.5 × that day's core weight from Thursday's close to Friday's 09:30 open. Cost: 1.25 NQ points per contract-equivalent
round trip. The second half of Gemini's idea (fade from the open to noon) is ALREADY the book's expiry rule (short NQ+ES
09:31–12:00), so it is not re-tested.
- Diagnostic: average Nasdaq night return on expiry Fridays vs all other Fridays, per era.
- Mark: strict vs G3, AND placebo test: 5,000 runs moving the same number of legs to random non-expiry Fridays within
  each year; fewer than 5% may beat V1's return in both eras.

**V2. Ridge penalty that grows with the training set (Gemini's patch to G3).** G3 uses a fixed penalty of 100 while its
training set grows, so it shrinks less and less over time. V2 sets the penalty to 0.2 × (number of training trades),
which equals 100 at the first fit (500 trades). One value, fixed now, no grid. Everything else is G3.
- Mark: strict vs G3 + luck test (5,000). Adopted only if the gain also clears the noise floor in both eras.

About 2 new trials (total about 296). Nothing here is blind.
