"""The pre-registered statistics plan for Race 1 (Amendment 9), written and run BEFORE any race data exists.

Test: a paired circular block bootstrap of the difference in annualised Sharpe ratios on DAILY returns (the idea in Ledoit and
Wolf, 2008: resample blocks of consecutive days, so calm and stormy spells stay together, and keep the two arms paired day by day).
Three main comparisons, Holm-corrected at 5%: AI vs 1x, AI vs the one-line rule, council (round 2) vs solo AI.
This script also checks the test on FAKE data:
  1. false alarms: when an 'AI' has no skill, how often would we wrongly declare it the winner? (must be about 5% or less)
  2. power: how big a Sharpe advantage can ~230 days actually detect 80% of the time?
Writes research/results/stats_plan.json; its sha256 goes in PREREGISTRATION.md. Never re-run after the freeze."""
import os, json, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = 20261109; DAYS = 230; BLOCK = 5; REPS = 2000; SIMS = 400; ALPHA = 0.05; MEANINGFUL = 0.30
rng = np.random.default_rng(SEED)
P = json.load(open(os.path.join(ROOT, 'data', 'portfolio.json')))
R = np.array([v[0] for d, v in sorted(P['daily_R'].items()) if '2021-07' <= d[:7] <= '2026-09'])     # the backtest book, daily R
def sharpe(x, axis=-1): s = x.std(axis=axis, ddof=1); return np.where(s > 0, x.mean(axis=axis) / np.where(s > 0, s, 1) * np.sqrt(252), 0.0)
def blocks(n, reps):
    starts = rng.integers(0, n, size=(reps, n // BLOCK + 1))
    return ((starts[:, :, None] + np.arange(BLOCK)) % n).reshape(reps, -1)[:, :n]
def pvalue(a, b, reps=REPS):
    """One-sided p-value that arm a's Sharpe beats arm b's (paired circular block bootstrap, shifted to the null)."""
    d0 = float(sharpe(a) - sharpe(b)); idx = blocks(len(a), reps)
    boot = sharpe(a[idx]) - sharpe(b[idx])
    return float(np.mean(boot - d0 >= d0)), d0
def holm(ps, alpha=ALPHA):
    order = np.argsort(ps); ok = [False] * len(ps)
    for k, i in enumerate(order):
        if ps[i] <= alpha / (len(ps) - k): ok[i] = True
        else: break
    return ok
SIZES = np.array([0.5, 1.0, 1.5, 2.0])
def race(skill):
    """One fake race: book days drawn from the backtest; the 'AI' picks bigger sizes on better days with strength `skill`."""
    r = rng.choice(R, DAYS); noise = rng.normal(size=DAYS)
    score = skill * (r - R.mean()) / R.std() + noise                       # skill = 0 -> sizes have nothing to do with returns
    ai = SIZES[np.clip(np.digitize(score, [-0.8, 0.0, 0.8]), 0, 3)]
    rule = rng.choice(SIZES, DAYS)                                          # stand-in rule with no skill either
    return r * ai, r, r * rule
def declares_winner(skill):
    a, one, rule = race(skill)
    p1, _ = pvalue(a, one, 600); p2, _ = pvalue(a, rule, 600)
    return all(holm([p1, p2, 1.0])[:2])
false_alarm = float(np.mean([declares_winner(0.0) for _ in range(SIMS)]))
power = {}
for skill in (0.15, 0.3, 0.45, 0.6):
    hits = [declares_winner(skill) for _ in range(SIMS // 2)]
    a, one, _ = race(skill); gap = float(np.mean([sharpe(race(skill)[0]) - sharpe(race(skill)[1]) for _ in range(200)]))
    power[str(skill)] = dict(sharpe_gap=round(gap, 2), power=round(float(np.mean(hits)), 2))
out = dict(written='2026-11-09', test='paired circular block bootstrap of the annualised Sharpe difference, daily returns, block 5 days, one-sided',
           comparisons=['AI vs 1x', 'AI vs one-line rule', 'council R2 vs solo AI'], correction='Holm at 5% across the three',
           pass_rule='AI vs 1x AND AI vs one-line rule both pass after Holm, in Race 1 and again in Race 2',
           meaningful_difference=f'+{MEANINGFUL} annualised Sharpe: smaller gaps are reported but not called important',
           race_days=DAYS, seed=SEED, fake_data_false_alarm_rate=round(false_alarm, 3), power_by_skill=power,
           note='Power shows the size of edge ~230 days can reliably detect; smaller real edges may be missed, so a "no" can mean "too small to see".')
p = os.path.join(ROOT, 'research', 'results', 'stats_plan.json'); json.dump(out, open(p, 'w'), indent=1); print(json.dumps(out, indent=1))
