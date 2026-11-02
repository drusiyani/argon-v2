# Retired: the per-setup AI desk (Oct 2026 - 3 Nov 2026)

Scout, Sceptic, Risk and the Chief judged fresh setups from Argon's original "liquidity sweep" strategy, scored against taking
every setup. Retired on 3 November 2026 without having judged a single setup:
- the strategy it judged had already been shown to lose money after realistic costs (+40.8R to −16.3R);
- GitHub's scheduler ran it too rarely for a setup to be under 30 minutes old when it looked (fixed on 29 Oct, still 0 calls).
Its job moved to the morning call (`engine/daytype.py`): Claude, plus the Gemini / Llama / GPT council, predicting trend or chop
days before the open, tested in the shadow. The code is kept here, unchanged, as part of the project's record.
