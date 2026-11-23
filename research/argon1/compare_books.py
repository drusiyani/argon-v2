"""Plain package vs G3 vs Argon-1 sizing vs both, on 2021-2023 (Argon-1's validation years; the test years stay closed).

Uses only public files: docs/data/cal/{year}.json (each day's account return at 0.5% per rules trade, every rules trade's
R and G3's keep/skip call) and research/results/argon1_val_preds.json (Argon-1's daily size from its 2011-2020 fit).
Rules P&L = 0.5% x sum of R; the rest of the day's return is the Nasdaq core, which no book changes.
Luck check: Argon-1's sizes shuffled across days 2,000 times (same mix of sizes, random days).
"""
import json, os, math
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RISK = 0.5


def stats(r):
    r = np.asarray(r) / 100; eq = np.cumprod(1 + r); dd = 1 - eq / np.maximum.accumulate(eq)
    yrs = len(r) / 252
    return dict(total=round((eq[-1] - 1) * 100, 1), cagr=round((eq[-1] ** (1 / yrs) - 1) * 100, 1),
                sharpe=round(float(r.mean() / r.std() * math.sqrt(252)), 2), worst_drop=round(float(dd.max()) * 100, 1))


def main(first='2021-01-01', last='2023-12-31'):
    P = json.load(open(os.path.join(ROOT, 'research', 'results', 'argon1_val_preds.json')))['days']
    days = []
    for y in range(int(first[:4]), int(last[:4]) + 1):
        for d, v in sorted(json.load(open(os.path.join(ROOT, 'docs', 'data', 'cal', f'{y}.json'))).items()):
            if first <= d <= last and d in P: days.append((d, v, P[d][1]))
    core, rules, rules_g3, size = [], [], [], []
    for d, v, s in days:
        R = sum(t[4] for t in v['t']); Rg = sum(t[4] for t in v['t'] if t[5])
        rules.append(RISK * R); rules_g3.append(RISK * Rg); core.append(v['r'] - RISK * R); size.append(s)
    core, rules, rules_g3, size = map(np.array, (core, rules, rules_g3, size))
    books = {'Plain package': core + rules, 'G3 (skips trades)': core + rules_g3,
             'Argon-1 sizing': core + size * rules, 'G3 + Argon-1': core + size * rules_g3}
    out = dict(period=[days[0][0], days[-1][0]], days=len(days), books={k: stats(v) for k, v in books.items()},
               size_mix={str(k): int((size == k).sum()) for k in (0.5, 1.0, 1.5, 2.0)})
    rng = np.random.default_rng(7); sh = []
    for _ in range(2000):
        sh.append(stats(core + rng.permutation(size) * rules)['sharpe'])
    a1 = out['books']['Argon-1 sizing']['sharpe']
    out['luck_check'] = dict(shuffled_sharpe_median=round(float(np.median(sh)), 2), shuffled_sharpe_95th=round(float(np.quantile(sh, .95)), 2),
                             share_of_shuffles_beating_argon1=round(float(np.mean(np.array(sh) >= a1)), 3))
    json.dump(out, open(os.path.join(ROOT, 'research', 'results', 'argon1_vs_g3.json'), 'w'), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
