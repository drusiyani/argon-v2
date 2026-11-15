# Batch 25 pre-registration (15 Nov 2026) — written and committed BEFORE any batch 25 code was run

Analysis only (does not touch the race). Gemini's T10 report: five proposals built on batch 24's G3 (Gemini's "P3").
About 250 trials so far; this adds 5. Source notes: Gemini supplied exact page/section quotes for the two Mesfin arXiv
papers; Claude still cannot open arXiv to confirm them. Several T10 citations are a Reddit post, an MQL5 product page and a
vendor documentation page; none of the tests below depends on them.

## Reference: G3 (batch 24), unchanged
Ridge (λ = 100, 24 features, monthly walk-forward) trained on friction-free R. Skip if (A) prediction in the bottom third of
the previous 252 predictions (needs 100) OR (B) prediction − 1.25 / stop distance ≤ 0.
Definitions used below: "stop" = the trade's risk in points; "trigger bar" = the 5 minutes ending at the minute before entry
(always on the 09:30 grid for these rules); "slot" = that bar's clock time.

## The five, exactly as coded
- **T1 stop inside noise (on top of G3).** Noise = mean range of the same slot over the previous 20 days (needs 20).
  Extra skip if stop < noise.
- **T2 remaining range (on top of G3).** ADR = mean 09:30–16:00 range over the previous 20 days. IDR = 09:30 open × (previous
  VXN close / 100) / √252 × 1.5958 (Gemini specified the 09:30 VXN; Argon only has closes: flagged). ESR = max(ADR, IDR).
  Used = 09:30 to trigger-minute range. Extra skip if max(0, ESR − Used) < stop + 1.25.
- **T3 dynamic friction (replaces G3's condition B).** Abdi–Ranaldo spread from the trigger bar and the bar before it:
  S = √max(0, 4·(c₋₁ − η₋₁)·(c₋₁ − η₀)), η = ½(ln H + ln L), c = ln close; points = S × trigger-bar close, capped at 1.50.
  For QuantLab there is no earlier bar in the session, so the last two 1-minute bars of the trigger (09:33 and 09:34) are
  used (flagged adaptation). RelVol = trigger-bar volume / mean volume of the same slot over the previous 20 days.
  Mult = max(1, 1/√max(0.1, RelVol)). Friction = (0.75 + max(0.50, points) × Mult) / stop.
  Skip if (A) as G3 OR prediction − Friction ≤ 0.
- **T4 two-stage model (replaces G3's predictor).** Same 24 features, monthly walk-forward, friction-free R.
  Stage 1: ridge (λ = 100) on 1[R > 0], prediction clipped to [0.05, 0.95]. Stage 2: ridge (λ = 200, Gemini's "at least 2×")
  on ln(1 + R) for winning trades only (needs 200); μ = exp(prediction) − 1. Loss = mean R of losing training trades.
  E = p·μ + (1 − p)·Loss. Then G3's two conditions, with E in place of the prediction.
- **T5 path efficiency (on top of G3).** Using 1-minute bars: QuantLab uses the five bars 09:30–09:34; other rules use the
  15 bars before entry. ER = |last close − first open| / (|first close − first open| + Σ |close change| over the rest).
  Extra skip if ER < 0.20.

## Marks (each judged against G3)
1. STRICT mark against G3 in both eras (better return and Sortino, worst drop no more than 1 point deeper, crash chance no
   more than 1 point higher; bootstrap as before).
2. Luck test, 5,000 draws, fewer than 5% may beat its return in BOTH eras. T1, T2, T5: the same number of EXTRA skips each
   year placed at random among the trades G3 keeps. T3, T4: their own skip decisions shuffled among each year's sized trades.
Adopt-candidate only if both pass. If more than one passes: report all, adopt none in this batch (a combined test would come
later, pre-registered).
Diagnostics reported whatever they show: extra skips per year; average R of the trades each one removes vs keeps, by period.

## Not allowed after seeing results
No changing any threshold, window, cap, λ, the adaptations above, or the marks.
