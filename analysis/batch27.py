"""Batch 27 (15 Nov 2026). Rule and marks: analysis/BATCH27_PREREG.md (committed before this file ran)."""
import os, json
A = os.path.dirname(os.path.abspath(__file__))
src24 = open(f'{A}/batch24.py').read()
exec(src24.split('# ---- vectorised package returns per era')[0])
exec(src24.split('# ---- vectorised package returns per era')[1].split('ELIG = {')[0])
def month_start(ym): return ym + '-01'
def minus12(ym): y, m = int(ym[:4]), int(ym[5:]); return f'{y - 1:04d}-{m:02d}-01'
judged = [r for r in rows if r['id'] in PRED]; OFF = {}
for ym in sorted({r['date'][:7] for r in judged}):
    lo, hi = minus12(ym), month_start(ym); w = [r for r in judged if lo <= r['date'] < hi]
    OFF[ym] = float(np.mean([FR[r['id']][0] for r in w]) - np.mean([PRED[r['id']] for r in w])) if len(w) >= 100 else 0.0
G3c = {}; hist = []
for r in rows:
    if r['id'] not in PRED: continue
    p = PRED[r['id']]; a_ = len(hist) >= 100 and p < np.quantile(hist[-252:], 1 / 3); b_ = (p + OFF[r['date'][:7]]) - 1.25 / FR[r['id']][1] <= 0
    G3c[r['id']] = 0.0 if (a_ or b_) else 1.0; hist.append(p)
REF = {e: full(ret(e, wvec(e, G3))) for e in ERAS}; H = {e: full(ret(e, wvec(e, G3c))) for e in ERAS}
st_ = all(strict(H[e], REF[e]) for e in ERAS)
rng = np.random.default_rng(20261118); N = 5000; by = collections.defaultdict(list)
for r in rows:
    if r['id'] in G3c: by[r['date'][:4]].append(r['id'])
tgt = {e: cagr(ret(e, wvec(e, G3c))) for e in ERAS}; hits = 0
for _ in range(N):
    sh = {}
    for y, L in by.items(): v = [G3c[i] for i in L]; rng.shuffle(v); sh.update(zip(L, v))
    hits += all(cagr(ret(e, wvec(e, sh))) >= tgt[e] for e in ERAS)
SUB = (('2010-13', 'lockbox2010', '2010', '2014'), ('2014-17', 'lockbox2010', '2014', '2018'), ('2018-20', 'lockbox2010', '2018', '2021'), ('2021-25', 'databento', '2021', '2026'), ('2026', 'databento', '2026', '2027'))
def subs(M):
    out = {}
    for lab, e, a, b in SUB:
        x = ret(e, wvec(e, M)); seg = [v for v, d in zip(x, E[e]['days']) if a <= d < b]; m = metrics(seg); out[lab] = f"{m['cagr_pct']:+.1f}% / {m['worst_drop_pct']:.1f}%"
    return out
TRm = {t['id']: t for e in ERAS for t in E[e]['tr']}; byyear = {}
for y in sorted(by):
    ids = by[y]; more = [i for i in ids if G3[i] == 1.0 and G3c[i] == 0.0]; fewer = [i for i in ids if G3[i] == 0.0 and G3c[i] == 1.0]
    byyear[y] = dict(offset=round(float(np.mean([OFF[TRm[i]['date'][:7]] for i in ids])), 3), extra_skips=len(more),
                     extra_skips_avg_R=round(float(np.mean([net(TRm[i]) for i in more])), 3) if more else None, extra_taken=len(fewer),
                     extra_taken_avg_R=round(float(np.mean([net(TRm[i]) for i in fewer])), 3) if fewer else None)
out = dict(G3=REF, G3c=H, strict_vs_G3=bool(st_), luck_random_beating_both_eras=int(hits), adopt_candidate=bool(st_ and hits / N < 0.05), sub_G3=subs(G3), sub_G3c=subs(G3c), by_year=byyear)
json.dump(out, open(f'{A}/batch27.json', 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
fmt = lambda h: f"{h['cagr_pct']:5.1f} {h['sortino']:4.2f} {h['worst_drop_pct']:6.1f} {h['boot']:5.1f}"
print('G3 ', ' | '.join(fmt(REF[e]) for e in ERAS)); print('G3c', ' | '.join(fmt(H[e]) for e in ERAS), 'strict', st_, 'luck', hits, 'ADOPT' if out['adopt_candidate'] else '')
print(out['sub_G3']); print(out['sub_G3c'])
for y, v in byyear.items(): print(y, v)
