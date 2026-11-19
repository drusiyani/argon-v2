# Batch 33 pre-registration: Gemini's two overconfidence fixes (19 Nov 2026)

Written before the test code ran. Not blind: prompted by July 2026. Diagnostic already run (Gemini's suggested
attribution): of G3's +0.09R July 2026 prediction jump, +0.043R came from "yesterday's rules result" (July mean −1.07R
vs −0.10R prior 18 months; weight negative), so losing days raised the next day's predictions.

**H1. Hinged yesterday's rules result.** Replace feature "yesterday rules R" by max(that value, 0) in training and
scoring. Nothing else changes. (Source of mechanism: Gemini, after Potters & Bouchaud 2005.)

**H2. Intraday variance ratio as a 25th feature.** From 1-minute NQ regular-session bars over the previous 20 trading
days (ending the day before): sum of squared 30-minute log returns divided by 6 × sum of squared 5-minute log returns;
feature = ln of that ratio. Everything else is G3. (Lo & MacKinlay 1988.)

Marks, each idea separately, all required to adopt:
1. Strict vs G3 in both eras + luck test under 5% (5,000).
2. Gain clears the noise floor (3 points 2021–26, 1.5 points 2010–20).
3. Sub-periods level or better in at least 4 of 5.
Reported: July 2026 at 0.625%, share of calls changed. About 2 new trials (total about 299).
