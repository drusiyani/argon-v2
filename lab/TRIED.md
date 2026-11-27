# Everything Argon has already tested (read this before proposing anything)

About 330 trials so far (multiple-testing count from batch 34 plus later batches). Every new idea raises the bar.
Data: NQ and ES futures, 1-minute prices (2010-2020 has NO volume, NO order book, NO options data), daily VIX/VXN,
T-bills, FOMC/macro calendar. Test eras: 2011-2020 (discover) and 2021/22-2026 (confirm once). Costs are real ticks.

## The live book (Amendment 13) — the thing any idea must improve
- Nasdaq core: long MNQ close to close, size = min(1.5, 1-year median VXN / VXN), plus pre-FOMC long, plus T-bill interest.
- Four intraday rules at 0.5% risk: QuantLab/Opening Drive (09:30-09:35 breakout), noise band (Zarattini 2024),
  ATR band, options-expiry rule. Fed-day skip. Cost cap 0.1R.
- AI desk sizes the rules 0-2x in a shadow book. Argon-1 (small transformer) is a shadow forecaster.

## Rejected (do NOT propose these or close variants)
**Pairs / spreads:** NQ-ES spread reversion (b8, b40).
**Fades / mean reversion:** calm-day fade (b8); prior-day VWAP rejection (b41).
**Momentum add-ons:** last half-hour momentum (b40); gap-continuation trade (b15); long-only breakouts (b4);
pyramiding (b6); QuantLab second chance (b18); QuantLab hold leg (b21).
**Sizing / regime tilts of the rules:** regime tilt (b9); overnight-after-down-day (b9); vol-managed package (b9);
opening-volatility sizing (b5); short gate by VXN (b5); day-after-win/loss reallocation (b12); gap-direction
reallocation / skip against gap (b11); gap-and-yesterday (b12); 8:30 news-shock and pre-market reallocation (b10);
reweighting rules (b6); long/short balance (b29).
**Filters / skips on the rules:** S&P confirmation (b10); expansion bar, VVG, GTBR dead zone, wick (b24);
stop-inside-noise, remaining range, path efficiency, dynamic friction (b25); mega-cap earnings freeze, 10:00 release
collision (b26); kill switches CUSUM / rolling PSR / Bayesian changepoint (b26); candle-shape facts (b29);
minimum stop (b35); noise-band gate on QuantLab (b6).
**Stops / exits:** every stop rule tried (b28); intraday stop on the core (b39).
**Core changes:** downside-vol core, recovery floor (b6); trend/200-day filter on core (b38); overnight-only core
(b40); day vs night split (b29); pre-settlement overnight leg (b31).
**Calendar:** turn of month (b40, nearest miss); pre-holiday (b40); plumbing calendar flags (b29).
**Models:** meta-labelling variants, recalibration, recency weighting, sibling labels, 4 alternative models,
two-stage model, growing ridge, faster skip line, overconfidence fixes (b13-b33). G3 itself was not proven after
counting trials (b34).
**Other markets:** S&P rules (friction kills it), other futures (round 1).
**Social-media setups:** SMC + fair value gap, two-candle 4H sweep (64% wins, ~0R) (b41).
**Other:** European-session noise band (b9); front-running the noise band's clock (b29); news-candle trades (b29);
dealer gamma regime (b18).

## Lessons (what kept killing ideas)
1. Costs: anything with many small trades dies after real ticks, especially 2010-2017.
2. Filters on the rules mostly cut big winners. Skipping helps a little; pressing doesn't.
3. Anything long-Nasdaq stacks onto the core's risk and fails the "both eras" bar.
4. Ideas tuned on 2021-26 fail on 2011-20. Discover on 2011-20 only.
5. Social-media patterns had no edge after costs.
