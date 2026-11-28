"""Batch 43: month-end stock-bond rebalancing trade on NQ (rules: analysis/BATCH43_PREREG.md)."""
import os, sys, json, math, csv, bisect, statistics as stt
A = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(A)
sys.path.insert(0, A); sys.path.insert(0, os.path.join(ROOT, 'research')); sys.path.insert(0, os.path.join(ROOT, 'engine'))
from batch42 import market, sr, corr, luck
COSTPTS = 1.1; WIN = 5

def main():
    import common as c
    from batch38 import rules_daily, stats
    ERA = c.DATA
    D, dl, _ = c.daily('NQ'); E, el, _ = c.daily('ES'); R = c.roll('NQ'); RE = c.roll('ES'); eset = set(el)
    zd, zr, _, _ = market('ZN')
    V = {}
    for row in csv.DictReader(open(os.path.join(ROOT, 'analysis', 'vxn.csv'))):
        try: V[row['date']] = float(row['vxn'])
        except ValueError: pass
    vk = sorted(V); rd = rules_daily()
    def ret(S, Sl, RR, k):
        d, p = Sl[k], Sl[k - 1]; r = (S[d]['c'] / S[d]['o'] - 1) if (d in RR or p in RR) else (S[d]['c'] / S[p]['c'] - 1)
        return 0.0 if abs(r) > 0.15 else r
    nq = {dl[k]: ret(D, dl, R, k) for k in range(1, len(dl))}
    es = {el[k]: ret(E, el, RE, k) for k in range(1, len(el))}
    # month ends (last NQ session of each month, not the very last session of the data)
    me = [k for k in range(len(dl) - 1) if dl[k + 1][:7] != dl[k][:7]]
    pos = {}; trades = []
    for a, b in zip(me, me[1:]):
        T = b; Ek = T - WIN
        if Ek <= a: continue
        prev, e_d = dl[a], dl[Ek]
        if prev not in eset or e_d not in eset: continue
        g = 1.0
        for x in el[bisect.bisect_right(el, prev):bisect.bisect_right(el, e_d)]: g *= 1 + es.get(x, 0.0)
        z = 1.0; lo, hi = bisect.bisect_right(zd, prev), bisect.bisect_right(zd, e_d)
        if hi - lo < 5: continue                                  # ZN data missing
        for i in range(lo, hi): z *= 1 + zr[i]
        rel = (g - 1) - (z - 1)
        side = -1 if rel > 0 else 1 if rel < 0 else 0
        if not side: continue
        cost = COSTPTS / D[e_d]['c']; tr = 0.0
        for j in range(Ek + 1, T + 1):
            r = side * nq[dl[j]] - (cost if j == Ek + 1 else 0.0); pos[dl[j]] = pos.get(dl[j], 0.0) + r; tr += r
        trades.append(dict(entry=e_d, exit=dl[T], side=side, rel_pct=round(rel * 100, 2), ret_pct=round(tr * 100, 3)))
    days = []; core = []
    for k in range(260, len(dl)):
        d, p = dl[k], dl[k - 1]
        i = bisect.bisect_left(vk, p)
        if i == 0: continue
        v = V[vk[i - 1]]; hist = sorted(V[x] for x in vk[max(0, i - 252):i]); w = min(1.5, hist[len(hist) // 2] / v)
        days.append(d); core.append(w * nq[d])
    book = [cv + rd.get(d, 0.0) for cv, d in zip(core, days)]
    idea = [pos.get(d, 0.0) for d in days]
    t_in = [t for t in trades if t['entry'] >= dl[259]]
    sb, sw = stats(book), stats([a + b for a, b in zip(book, idea)])
    def side_stats(s):
        x = [t['ret_pct'] for t in t_in if t['side'] == s]
        return dict(n=len(x), win_rate=round(sum(v > 0 for v in x) / len(x), 3) if x else None, avg_pct=round(stt.mean(x), 3) if x else None)
    out = dict(era=ERA, period=[days[0], days[-1]], book=sb, book_with_it=sw, sharpe_gain=round(sw['sharpe'] - sb['sharpe'], 3),
               passes_this_era=sw['sharpe'] > sb['sharpe'],
               idea=dict(trades=len(t_in), win_rate=round(sum(t['ret_pct'] > 0 for t in t_in) / len(t_in), 3) if t_in else None,
                         avg_ret_pct_after_costs=round(stt.mean(t['ret_pct'] for t in t_in), 3) if t_in else None,
                         own_sharpe=sr(idea), corr_with_book=corr(idea, book), corr_with_core=corr(idea, core),
                         short_side=side_stats(-1), long_side=side_stats(1)),
               luck=luck(book, idea), trial_count_approx=332, trades=t_in)
    json.dump(out, open(f'{A}/batch43_{ERA}.json', 'w'), indent=1); print(json.dumps({k: v for k, v in out.items() if k != 'trades'}, indent=1))

if __name__ == '__main__': main()
