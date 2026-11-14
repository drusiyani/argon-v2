"""Batch 16 (14 Nov 2026). Rules and mark: analysis/BATCH16_PREREG.md (committed before this file ran).
Reads the batch 14 cache and rebuilds the walk-forward model exactly as batch 14."""
import os, json, math
A = os.path.dirname(os.path.abspath(__file__))
exec(open(f'{A}/batch14.py').read().split('# ---- Part A')[0])
order = sorted([r for r in NQ if r['id'] in W1m], key=lambda r: (r['date'], E[r['id'][0]]['tr'][r['id'][1]]['entry_min']))
R1 = {i: (0.5 if m == 0.5 else 1.0) for i, m in W1m.items()}; R2 = {i: (0.0 if m == 0.5 else 1.0) for i, m in W1m.items()}
R3 = {}; hist = []
for r in order:
    m = W1m[r['id']]; R3[r['id']] = m / (sum(hist[-250:]) / len(hist[-250:])) if len(hist) >= 100 else m; hist.append(m)
def series(e, mult=None):
    z = E[e]['z']; risk = z['risk']; R = collections.defaultdict(float)
    for t in E[e]['tr']: R[t['date']] += (mult.get(t['id'], 1.0) if (mult is not None and mom(t) and t['sym'] == 'NQ') else 1.0) * net(t)
    return [E[e]['core'][d] + 0.5 * risk * R.get(d, 0.0) + z['tb'][d] for d in E[e]['days']]
B0 = {e: dict(metrics(series(e)), boot=boot(series(e))) for e in ERAS}
def score(name, mult):
    out = {'name': name}
    for e in ERAS:
        x = series(e, mult); h = dict(metrics(x), boot=boot(x)); b = B0[e]
        h['strict'] = bool(h['cagr_pct'] > b['cagr_pct'] and h['sortino'] > b['sortino'] and h['worst_drop_pct'] >= b['worst_drop_pct'] - 1 and h['boot'] <= b['boot'] + 1)
        tr = [t for t in E[e]['tr'] if mom(t) and t['sym'] == 'NQ' and t['date'] in E[e]['ds']]
        h['avg_size'] = round(sum(mult.get(t['id'], 1.0) for t in tr) / len(tr), 3) if mult else 1.0; out[e] = h
    out['strict_both'] = out['databento']['strict'] and out['lockbox2010']['strict']; return out
RES = collections.OrderedDict([('baseline', score('package baseline', None)), ('W1m', score('model x0.5/x1/x1.5 (batch 14 candidate)', W1m)),
                               ('R1', score('R1 cut-only', R1)), ('R2', score('R2 skip-only', R2)), ('R3', score('R3 size-neutral', R3))])
passed = [k for k in ('R1', 'R2', 'R3') if RES[k]['strict_both']]
pick = max(passed, key=lambda k: RES[k]['databento']['worst_drop_pct'] + RES[k]['lockbox2010']['worst_drop_pct']) if passed else None
# diagnostics: what the cut trades are, and what they did on the core's worst days (the crash-hedge question)
diag = {}
for e in ERAS:
    z = E[e]['z']; cut = [t for t in E[e]['tr'] if R1.get(t['id']) == 0.5 and t['date'] in E[e]['ds']]; allm = [t for t in E[e]['tr'] if mom(t) and t['sym'] == 'NQ' and t['date'] in E[e]['ds']]
    worst = set(sorted(E[e]['days'], key=lambda d: E[e]['core'][d])[:len(E[e]['days']) // 20]); sh = lambda L: round(100 * sum(1 for t in L if t['side'] not in (1, 'long')) / len(L), 1)
    diag[e] = dict(cut_trades=len(cut), all_trades=len(allm), cut_share_pct=round(100 * len(cut) / len(allm), 1), short_share_of_cut_pct=sh(cut), short_share_of_all_pct=sh(allm),
                   cut_avg_R=round(sum(net(t) for t in cut) / len(cut), 3), cut_trades_R_on_core_worst_5pct_days=round(sum(net(t) for t in cut if t['date'] in worst), 1),
                   all_trades_R_on_core_worst_5pct_days=round(sum(net(t) for t in allm if t['date'] in worst), 1))
json.dump(dict(baseline=B0, results=RES, passed=passed, candidate=pick, diagnostics=diag), open(f'{A}/batch16.json', 'w'), indent=1)
for k, r in RES.items():
    d, l = r['databento'], r['lockbox2010']
    print(f"{r['name'][:40]:40s} | {d['cagr_pct']:5.1f} {d['sharpe']:4.2f} {d['sortino']:4.2f} {d['worst_drop_pct']:6.1f} {d['boot']:4.1f} sz {d['avg_size']} | {l['cagr_pct']:5.1f} {l['sharpe']:4.2f} {l['sortino']:4.2f} {l['worst_drop_pct']:6.1f} {l['boot']:4.1f} sz {l['avg_size']} | strict {r['strict_both']} ({d['strict']},{l['strict']})")
print('passed', passed, 'candidate', pick); print(json.dumps(diag, indent=0))
