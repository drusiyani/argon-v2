# Decisions

#argon/decisions · [[Home]]

Why Argon v2 is built the way it is. Every rule change is also logged as a numbered amendment in `PREREGISTRATION.md`.

| when | decision | why |
|---|---|---|
| Oct 2026 | Four pre-registered intraday rules on NQ and ES futures; the AI sizes trades instead of picking them | a once-a-day call is a fair, testable job for an AI |
| 28 Oct 2026 | Opened the sealed 2011-2020 data once: the book lost money; published it | honesty; that data can no longer be a clean test |
| Nov 2026 | Nightly hash-chained ledger, rebuilt every night (replay check), phone alerts | nobody, including Dru, can quietly change a result |
| Nov 2026 | Freeze moved from 31 Dec to **31 Jan 2027**; Race 1 runs Feb-Dec 2027 | learn from v1's results first; every change before the freeze is logged |
| Nov 2026 | Top generally-available model from each company races, chosen on the freeze date; upgrades only between races | fairness: no AI gets a newer model mid-race |
| Nov 2026 | Solo AI = Claude Opus 5.5; council = Claude, Gemini 4 Argon, GPT-6 Astra, **DeepSeek V4 Pro** (replacing Llama) via OpenRouter | Llama went enterprise-only; DeepSeek is the most different model, which is what the council tests |
| 7 Nov 2026 | Fixed the morning call: Claude 5.5 rejects `temperature` (400 errors); errors are now saved | every call had silently failed |
| Nov 2026 | Same effort level for every AI, no sampling settings | fairness between models |
| Nov 2026 | Sizes 0.5x / 1x / 1.5x / **2x**; one-line rule also reaches 2x; at most **6%** risk in a day | a wider range shows the AI's skill more clearly; the cap stops a bad day sinking the account |
| Nov 2026 | Each AI sees a short **track record** of its own past calls (not the Brain's notes) | lets it calibrate; kept short to save cost; shared commentary would muddy the test |
| Nov 2026 | **Two-round council**: independent private answers, then an anonymous discussion and a final private answer; both scored | tests whether discussion helps or just causes herding |
| Nov 2026 | **Random sizer** as a 'luck' competitor (seed fixed in advance) | if the AIs can't beat random, they have no skill |
| Nov 2026 | Headlines since the previous close from two sources; suspicious ones are hidden and logged | the AIs should read news (their strength) without being hijacked by it |
| Nov 2026 | Prompt caching on the solo AI's three repeat calls | same answers, lower cost |
| Nov 2026 | Every trading day gets a Brain note; this page records the reasons | a readable trail for the write-up and the interview |
