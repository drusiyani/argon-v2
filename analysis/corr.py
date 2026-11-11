"""Analysis only (does not touch the race): how do the rules move with the Nasdaq?
Correlation of the book's daily result with the Nasdaq's daily return, overall and on the index's worst/best days,
per era and per rule. Uses the official book code unchanged (full history, both eras). Writes analysis/corr.json.
No sizing or mix is chosen here: that needs pass marks written down first."""
import os, sys, json, math, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'engine'))
import portfolio as P
c = P.c
tr = P.book(1.0)
net = lambda t: t['w'] * (t['gross'] - t['cost'])
D, dl, _ = c.daily('NQ')
skip = set()
for f in ('roll', 'bad_days'):
    try:
        v = getattr(c, f)('NQ'); v = v.keys() if isinstance(v, dict) else v
        skip |= {x for x in v if isinstance(x, str) and len(x) == 10}
    except Exception as ex: print(f, 'not used:', ex)
idx_c2c, idx_o2c = {}, {}
for k in range(1, len(dl)):
    d, p = dl[k], dl[k - 1]
    idx_o2c[d] = D[d]['c'] / D[d]['o'] - 1
    if d not in skip and p not in skip:
        r = D[d]['c'] / D[p]['c'] - 1
        if abs(r) < 0.15: idx_c2c[d] = r          # guard against a roll jump that slipped through
print('daily bars', len(dl), dl[:1], dl[-1:], 'skip', len(skip), 'c2c days', len(idx_c2c), 'trade dates', min(t['date'] for t in tr), max(t['date'] for t in tr))
book = collections.defaultdict(float); rule = collections.defaultdict(lambda: collections.defaultdict(float))
for t in tr: book[t['date']] += net(t); rule[t['strat']][t['date']] += net(t)

def corr(a, b):
    n = len(a)
    if n < 20: return None
    ma, mb = sum(a) / n, sum(b) / n
    va = sum((x - ma) ** 2 for x in a); vb = sum((y - mb) ** 2 for y in b)
    return round(sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(va * vb), 3) if va and vb else None

def era_stats(lo, hi):
    days = [d for d in sorted(idx_c2c) if lo <= d <= hi]
    if len(days) < 60: return dict(days=len(days), note='not enough index days in this range')
    ix = [idx_c2c[d] for d in days]; bk = [book.get(d, 0.0) for d in days]
    q = sorted(ix); lo5, hi5 = q[int(0.05 * len(q))], q[int(0.95 * len(q))]
    worst = [d for d in days if idx_c2c[d] <= lo5]; best = [d for d in days if idx_c2c[d] >= hi5]
    mid = [d for d in days if lo5 < idx_c2c[d] < hi5]
    sh = lambda x: round(sum(x) / len(x) / (math.sqrt(sum((v - sum(x) / len(x)) ** 2 for v in x) / (len(x) - 1)) or 1) * math.sqrt(252), 2)
    mk = collections.defaultdict(lambda: [1.0, 0.0])
    for d in days: mk[d[:7]][0] *= 1 + idx_c2c[d]; mk[d[:7]][1] += book.get(d, 0.0)
    ms = sorted(mk)
    return dict(days=len(days),
        corr_daily_close_to_close=corr(bk, ix),
        corr_daily_intraday=corr(bk, [idx_o2c[d] for d in days]),
        corr_monthly=corr([mk[m][1] for m in ms], [mk[m][0] - 1 for m in ms]),
        worst_5pct_index_days=dict(n=len(worst), index_avg_pct=round(100 * sum(idx_c2c[d] for d in worst) / len(worst), 2),
                                   book_avg_R=round(sum(book.get(d, 0) for d in worst) / len(worst), 3), book_total_R=round(sum(book.get(d, 0) for d in worst), 1)),
        best_5pct_index_days=dict(n=len(best), index_avg_pct=round(100 * sum(idx_c2c[d] for d in best) / len(best), 2),
                                  book_avg_R=round(sum(book.get(d, 0) for d in best) / len(best), 3), book_total_R=round(sum(book.get(d, 0) for d in best), 1)),
        middle_90pct_days=dict(book_avg_R=round(sum(book.get(d, 0) for d in mid) / len(mid), 3), book_total_R=round(sum(book.get(d, 0) for d in mid), 1)),
        sharpe_book=sh(bk), sharpe_index=sh(ix),
        per_rule_corr_daily={s: corr([rule[s].get(d, 0.0) for d in days], ix) for s in sorted(rule)})

first = min(idx_c2c); last = max(idx_c2c)
out = dict(note='Backtest, after costs. Book result in R per day (1R = 1% at current sizing). Index = Nasdaq futures regular session, '
                'close to close, roll days excluded. Read-only analysis; chooses nothing.',
           range=[first, last], sealed_2011_2020=era_stats('2011-01-01', '2020-12-31'), built_2021_2026=era_stats('2021-01-01', '2026-12-31'),
           year_2026=era_stats('2026-01-01', '2026-12-31'), all=era_stats(first, last))
json.dump(out, open(os.path.join(ROOT, 'analysis', 'corr.json'), 'w'), indent=1)
print(json.dumps(out, indent=1))
