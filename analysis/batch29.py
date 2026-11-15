"""Batch 29 (15-16 Nov 2026): "the unknown". Rules and marks: analysis/BATCH29_PREREG.md (committed before this file ran).
Needs the batch 14 and 24 caches plus analysis/_cache/batch29_{era}.pkl from batch29_dump.py."""
import os, sys, re, json, pickle, datetime as dt
A = os.path.dirname(os.path.abspath(__file__)); src24 = open(f'{A}/batch24.py').read().split('# ---- vectorised package returns per era')
exec(src24[0]); exec(src24[1].split('ELIG = {')[0])
sys.path.insert(0, os.path.join(os.path.dirname(A), 'research')); import common as cm          # only for the monthly re-pick function
C29 = {e: pickle.load(open(f'{A}/_cache/batch29_{e}.pkl', 'rb')) for e in ERAS}
rng = np.random.default_rng(20261116); N = 5000; CAP = 0.10; OUT = collections.OrderedDict()
IDX = {e: {t['id']: i for i, t in enumerate(Q[e]['tr'])} for e in ERAS}; TR = {t['id']: t for e in ERAS for t in E[e]['tr']}
side = lambda t: 1 if t['side'] in (1, 'long') else -1
def wfast(Gmap):
    w = {e: np.ones(len(Q[e]['tr'])) for e in ERAS}
    for i, v in Gmap.items():
        k = IDX[i[0]].get(i)
        if k is not None and Q[i[0]]['mom'][k]: w[i[0]][k] = v
    return w
def ret2(e, w, base=None, extra=None):
    q = Q[e]; r = (q['base'] if base is None else base) + 0.5 * q['risk'] * np.bincount(q['day'], weights=w * q['nr'], minlength=q['nd'])
    return r if extra is None else r + 0.5 * q['risk'] * extra
WG3 = wfast(G3); REF = {e: full(ret2(e, WG3[e])) for e in ERAS}
def luck(Gmap, n=N):
    """Shuffle the idea's per-trade multipliers within each year; count random versions beating its return in both eras."""
    by = collections.defaultdict(list); w0 = wfast(Gmap); tgt = {e: cagr(ret2(e, w0[e])) for e in ERAS}
    for i, v in Gmap.items():
        k = IDX[i[0]].get(i)
        if k is not None and Q[i[0]]['mom'][k]: by[(i[0], Q[i[0]]['yr'][k])].append((k, v))
    grp = [(e, np.array([a for a, _ in L]), np.array([b for _, b in L])) for (e, _), L in by.items()]; hits = 0
    for _ in range(n):
        w = {e: np.ones(len(Q[e]['tr'])) for e in ERAS}
        for e, ix, v in grp: w[e][ix] = rng.permutation(v)
        hits += all(cagr(ret2(e, w[e])) >= tgt[e] for e in ERAS)
    return hits
def judge(name, res, lk=None, **more):
    ok = all(strict(res[e], REF[e]) for e in ERAS); d = dict(result=res, strict_vs_G3=bool(ok), **more)
    if lk is not None: d.update(luck_random_beating_both_eras=int(lk), luck_pass=bool(lk / N < 0.05), adopt_candidate=bool(ok and lk / N < 0.05))
    else: d.update(adopt_candidate=bool(ok))
    OUT[name] = d; print(name, ' | '.join(fmt(res[e]) for e in ERAS), 'strict', ok, 'luck', lk, flush=True); return ok
fmt = lambda h: f"{h['cagr_pct']:5.1f} {h['sortino']:4.2f} {h['worst_drop_pct']:6.1f} {h['boot']:5.1f}"
print('package', ' | '.join(fmt(BASE[e]) for e in ERAS)); print('G3     ', ' | '.join(fmt(REF[e]) for e in ERAS), flush=True)
OUT['reference'] = dict(package=BASE, G3=REF)

# ---------------------------------------------------------------- the G3 pipeline as a function (must reproduce G3 exactly)
def pipeline(label=None, feat=None, weight=None):
    lab = label or {i: v[0] for i, v in FR.items()}; ft = feat or (lambda r: r['f']); PR = {}
    for P_ in sorted({r['date'][:7] for r in rows}):
        trn = [r for r in rows if r['date'][:7] < P_]; tst = [r for r in rows if r['date'][:7] == P_]
        if len(trn) < 500 or not tst: continue
        X = np.array([ft(r) for r in trn]); y = np.array([lab[r['id']] for r in trn]); mu, sd = X.mean(0), X.std(0); sd[sd == 0] = 1
        S = np.c_[np.ones(len(X)), (X - mu) / sd]; pen = np.eye(X.shape[1] + 1) * 100.0; pen[0, 0] = 0
        if weight is None: b = np.linalg.solve(S.T @ S + pen, S.T @ y)
        else:
            w = np.array([weight(r['date'], P_) for r in trn]); w = w * len(w) / w.sum()          # mean weight 1, so the penalty keeps its meaning
            b = np.linalg.solve(S.T @ (S * w[:, None]) + pen, S.T @ (w * y))
        for r in tst: PR[r['id']] = float(np.r_[1.0, (np.array(ft(r)) - mu) / sd] @ b)
    G = {}; hist = []
    for r in rows:
        if r['id'] not in PR: continue
        p = PR[r['id']]; a_ = len(hist) >= 100 and p < np.quantile(hist[-252:], 1 / 3); b_ = p - 1.25 / FR[r['id']][1] <= 0
        G[r['id']] = 0.0 if (a_ or b_) else 1.0; hist.append(p)
    return G, PR
Gchk, _ = pipeline(); assert Gchk == G3, 'pipeline() does not reproduce G3'
def model_test(name, G, **more):
    w = wfast(G); res = {e: full(ret2(e, w[e])) for e in ERAS}
    more['skip_share'] = {e: round(1 - float(np.mean([G[i] for i in G if i[0] == e])), 3) for e in ERAS}
    more['agree_with_G3'] = round(float(np.mean([G[i] == G3[i] for i in G if i in G3])), 3)
    return judge(name, res, luck(G), **more)

# ---------------------------------------------------------------- U1: shifted noise-band clock
def nbbook(e, key):
    picked = [t for t in cm.walkforward(C29[e]['net'][key]) if t['cost'] <= CAP]
    fr = {(t['date'], t['variant'], t['entry_min']): t['gross'] for t in C29[e]['free'][key]}
    for t in picked: t['free'] = fr.get((t['date'], t['variant'], t['entry_min']))
    return picked
def pkg_with(e, nb):
    q = Q[e]; days = E[e]['days']; di = {d: k for k, d in enumerate(days)}; w = np.ones(len(q['tr'])); w[q['strat'] == 'noiseband'] = 0.0
    x = np.zeros(q['nd'])
    for t in nb:
        if t['date'] in di: x[di[t['date']]] += t['gross'] - t['cost']
    return ret2(e, w, extra=x)
PER = (('2010-20', '2010-07-01', '2021-01-01', 10.5), ('2021 to May 2024', '2021-01-01', '2024-06-01', 3.42), ('Jun 2024 to Nov 2026', '2024-06-01', '2027-01-01', 2.46))
u1 = {}; NBK = {}
for key in ('noiseband', 'nb_E5', 'nb_L5'):
    NBK[key] = {e: nbbook(e, key) for e in ERAS}; allt = [t for e in ERAS for t in NBK[key][e]]
    u1[key] = dict(package={e: full(pkg_with(e, NBK[key][e])) for e in ERAS},
                   per_year={lab: dict(trades=round(sum(1 for t in allt if a <= t['date'] < b) / yrs), net_R=round(sum(t['gross'] - t['cost'] for t in allt if a <= t['date'] < b) / yrs, 1),
                                       free_R=round(sum(t['free'] for t in allt if a <= t['date'] < b and t['free'] is not None) / yrs, 1)) for lab, a, b, yrs in PER})
    print('U1', key, ' | '.join(fmt(u1[key]['package'][e]) for e in ERAS), u1[key]['per_year'], flush=True)
b0 = u1['noiseband']['package']; e5 = u1['nb_E5']['package']; l5 = u1['nb_L5']['package']
u1['official_package_for_check'] = BASE
u1['E5_strict_vs_package'] = bool(all(strict(e5[e], b0[e]) for e in ERAS)); u1['E5_beats_L5_both_eras'] = bool(all(e5[e]['cagr_pct'] > l5[e]['cagr_pct'] for e in ERAS))
u1['stage1_pass'] = bool(u1['E5_strict_vs_package'] and u1['E5_beats_L5_both_eras']); u1['L5_strict_vs_package'] = bool(all(strict(l5[e], b0[e]) for e in ERAS))
OUT['U1_published_clock'] = u1; print('U1 stage 1', u1['stage1_pass'], 'E5 strict', u1['E5_strict_vs_package'], 'L5 strict', u1['L5_strict_vs_package'], flush=True)

# ---------------------------------------------------------------- U2: sibling labels
SIB = {e: collections.defaultdict(list) for e in ERAS}
for e in ERAS:
    for k in ('quantlab', 'noiseband', 'atrband'):
        for t in C29[e]['free'][k]: SIB[e][(k, t['date'], t['entry_min'], side(t))].append(t['gross'] * t['risk_pts'])
lab2 = {}; nsib = collections.Counter(); miss = 0
for r in rows:
    t = TR[r['id']]; L = SIB[r['id'][0]].get((t['strat'], t['date'], t['entry_min'], side(t)))
    if not L: lab2[r['id']] = FR[r['id']][0]; miss += 1; continue
    lab2[r['id']] = float(np.mean(L)) / t['risk_pts']; nsib[(t['strat'], min(len(L), 8))] += 1
G_u2, P_u2 = pipeline(label=lab2)
own = np.array([FR[r['id']][0] for r in rows]); sl = np.array([lab2[r['id']] for r in rows])
model_test('U2_sibling_labels', G_u2, rows_without_siblings=miss, label_sd=dict(own=round(float(own.std()), 3), sibling=round(float(sl.std()), 3)), corr_own_vs_sibling=round(float(np.corrcoef(own, sl)[0, 1]), 3))

# ---------------------------------------------------------------- U3: QuantLab pick skill + six-variant ensemble
u3 = {}; res3 = {}
for e in ERAS:
    q = Q[e]; di = {d: k for k, d in enumerate(E[e]['days'])}; book_ql = [t for t in q['tr'] if t['strat'] == 'quantlab']; months = {t['month'] for t in cm.walkforward(C29[e]['net']['quantlab'])}
    fr = {(t['date'], t['variant'], t['entry_min']): t['gross'] for t in C29[e]['free']['quantlab']}
    sib = [t for t in C29[e]['net']['quantlab'] if t['month'] in months and t['date'] in di]
    pk = [t for t in cm.walkforward(C29[e]['net']['quantlab']) if t['date'] in di]
    dec = {t['date']: G3.get(t['id'], 1.0) for t in book_ql}
    x = np.zeros(q['nd'])
    for t in sib:
        if t['cost'] <= CAP: x[di[t['date']]] += dec.get(t['date'], 1.0) * (t['gross'] - t['cost']) / 6
    w = WG3[e].copy(); w[q['strat'] == 'quantlab'] = 0.0; res3[e] = full(ret2(e, w, extra=x)); yrs = len(E[e]['days']) / 252
    u3[e] = dict(picked_net_R_per_year=round(sum(t['gross'] - t['cost'] for t in pk if t['cost'] <= CAP) / yrs, 1), six_average_net_R_per_year=round(sum((t['gross'] - t['cost']) / 6 for t in sib if t['cost'] <= CAP) / yrs, 1),
                 picked_free_R_per_year=round(sum(fr.get((t['date'], t['variant'], t['entry_min']), t['gross']) for t in pk) / yrs, 1), six_average_free_R_per_year=round(sum(fr.get((t['date'], t['variant'], t['entry_min']), t['gross']) / 6 for t in sib) / yrs, 1),
                 picked_cost_rule_removed=round(float(np.mean([t['cost'] > CAP for t in pk])), 3), siblings_cost_rule_removed=round(float(np.mean([t['cost'] > CAP for t in sib])), 3))
judge('U3_quantlab_six_variant_ensemble', res3, pick_skill=u3); print('   pick skill', u3, flush=True)

# ---------------------------------------------------------------- U4: shape of the signal candle
def shape(r):
    t = TR[r['id']]
    if t['strat'] != 'quantlab': return [0.0, 0.0, 0.0]
    B = [b for b in C29[r['id'][0]]['m1'].get(t['date'], []) if 570 <= b[0] <= 574]
    if len(B) < 5: return [0.0, 0.0, 0.0]
    o, c_ = B[0][1], B[-1][4]; hi = max(b[2] for b in B); lo = min(b[3] for b in B); s = side(t)
    clv = s * (2 * (c_ - lo) / (hi - lo) - 1) if hi > lo else 0.0; sh = clip((c_ - B[-2][4]) / (c_ - o), 2) if c_ != o else 0.0
    v0, v1 = B[0][5] + B[1][5], B[3][5] + B[4][5]; lv = math.log(v1 / v0) if v0 > 0 and v1 > 0 else 0.0
    return [clv, sh, clip(lv, 3)]
SH = {r['id']: shape(r) for r in rows}
G_u4, _ = pipeline(feat=lambda r: r['f'] + SH[r['id']]); model_test('U4_signal_candle_shape', G_u4)

# ---------------------------------------------------------------- U5: recency weighting (3-year half-life)
def rw(d, P_): return 0.5 ** (((dt.date.fromisoformat(P_ + '-01') - dt.date.fromisoformat(d)).days / 365.25) / 3)
G_u5, _ = pipeline(weight=rw); model_test('U5_recency_weighting', G_u5)

# ---------------------------------------------------------------- U6: long x0.75, short x1.25 under G3
G_u6 = {}
for e in ERAS:
    for k, t in enumerate(Q[e]['tr']):
        if Q[e]['mom'][k]: G_u6[t['id']] = G3.get(t['id'], 1.0) * (0.75 if side(t) == 1 else 1.25)
w6 = wfast(G_u6); res6 = {e: full(ret2(e, w6[e])) for e in ERAS}
# luck twin: shuffle only the 0.75/1.25 labels within each year, keeping G3's keep/skip calls fixed
by6 = collections.defaultdict(list); tgt6 = {e: cagr(ret2(e, w6[e])) for e in ERAS}
for e in ERAS:
    for k, t in enumerate(Q[e]['tr']):
        if Q[e]['mom'][k]: by6[(e, Q[e]['yr'][k])].append((k, 0.75 if side(t) == 1 else 1.25))
grp6 = [(e, np.array([a for a, _ in L]), np.array([b for _, b in L])) for (e, _), L in by6.items()]; hits6 = 0
for _ in range(N):
    w = {e: WG3[e].copy() for e in ERAS}
    for e, ix, v in grp6: w[e][ix] = WG3[e][ix] * rng.permutation(v)
    hits6 += all(cagr(ret2(e, w[e])) >= tgt6[e] for e in ERAS)
ls = {}
for e in ERAS:
    q = Q[e]; m = q['mom'] & (WG3[e] > 0); sd_ = np.array([side(t) for t in q['tr']]); core = np.array([E[e]['core'][d] for d in E[e]['days']])
    dayL = np.bincount(q['day'], weights=m * (sd_ == 1) * q['nr'], minlength=q['nd']); dayS = np.bincount(q['day'], weights=m * (sd_ == -1) * q['nr'], minlength=q['nd'])
    ls[e] = dict(long_trades=int((m & (sd_ == 1)).sum()), long_avg_R=round(float(q['nr'][m & (sd_ == 1)].mean()), 3), short_trades=int((m & (sd_ == -1)).sum()), short_avg_R=round(float(q['nr'][m & (sd_ == -1)].mean()), 3),
                 corr_long_R_with_core=round(float(np.corrcoef(dayL, core)[0, 1]), 3), corr_short_R_with_core=round(float(np.corrcoef(dayS, core)[0, 1]), 3))
judge('U6_long_short_balance', res6, hits6, long_vs_short=ls); print('  ', ls, flush=True)

# ---------------------------------------------------------------- U7: day vs night core
u7 = {}; legs = {}
for e in ERAS:
    z = E[e]['z']; D = z['D']; dl = z['dl']; pos = {d: k for k, d in enumerate(dl)}; night, day, px = [], [], []
    for d in E[e]['days']:
        r = z['ret'][d]; o, h, l, c_ = D[d]; dy = c_ / o - 1
        if r == 0.0: dy = 0.0; ng = 0.0
        else: ng = (1 + r) / (1 + dy) - 1
        night.append(ng); day.append(dy); px.append(o)
    night, day, px = np.array(night), np.array(day), np.array(px); legs[e] = (night, day, px)
    st = lambda x: dict(ann_return_pct=round(100 * float(x.mean()) * 252, 1), ann_vol_pct=round(100 * float(x.std()) * math.sqrt(252), 1), sharpe=round(float(x.mean() / x.std() * math.sqrt(252)), 2))
    u7[e] = dict(night=st(night), day=st(day), corr_night_day=round(float(np.corrcoef(night, day)[0, 1]), 3))
unlock7 = all(u7[e]['night']['sharpe'] > u7[e]['day']['sharpe'] for e in ERAS); u7['rule_unlocked'] = bool(unlock7); print('U7', u7, flush=True)
if unlock7:
    res7 = {}; res7free = {}
    for e in ERAS:
        z = E[e]['z']; night, day, px = legs[e]; w = np.array([z['w'][d] for d in E[e]['days']]); fom = np.array([z['fomc'].get(d, 0.0) for d in E[e]['days']]); tb = np.array([z['tb'][d] for d in E[e]['days']])
        core = w * (1.25 * night + 0.75 * day) + fom; cost = w * 1.25 / px
        res7[e] = full(ret2(e, WG3[e], base=core - cost + tb)); res7free[e] = full(ret2(e, WG3[e], base=core + tb))
    judge('U7_night_heavy_core', res7, diagnostic=u7, before_switching_costs=res7free)
else: OUT['U7_night_heavy_core'] = dict(diagnostic=u7, adopt_candidate=False, note='rule not unlocked')

# ---------------------------------------------------------------- U8: the trade model as a forecast for the core
first = {}
for r in rows:
    if r['id'] in PRED and r['date'] not in first: first[r['date']] = (PRED[r['id']], FR[r['id']][2], r['id'][0])
hist = []; T8 = {}
for d in sorted(first):
    p, em, e = first[d]
    if len(hist) >= 100:
        lo, hi = np.quantile(hist[-252:], [1 / 3, 2 / 3]); B = C29[e]['m1'].get(d)
        if B:
            b0 = [b for b in B if b[0] >= em]
            if b0: T8[d] = (e, 0 if p < lo else (2 if p > hi else 1), B[-1][4] / b0[0][1] - 1, b0[0][1])
    hist.append(p)
u8 = {}
for e in ERAS:
    u8[e] = {}
    for k, nm in ((0, 'bottom'), (1, 'middle'), (2, 'top')):
        x = np.array([v[2] for v in T8.values() if v[0] == e and v[1] == k]); u8[e][nm] = dict(days=len(x), mean_bp=round(1e4 * float(x.mean()), 1), vol_bp=round(1e4 * float(x.std()), 1))
unlock8 = all(u8[e]['top']['mean_bp'] < u8[e]['bottom']['mean_bp'] and u8[e]['top']['vol_bp'] > u8[e]['bottom']['vol_bp'] for e in ERAS); u8['rule_unlocked'] = bool(unlock8); print('U8', u8, flush=True)
if unlock8:
    res8 = {}
    for e in ERAS:
        z = E[e]['z']; base = Q[e]['base'].copy()
        for k, d in enumerate(E[e]['days']):
            v = T8.get(d)
            if v and v[1] == 2: base[k] += -0.25 * z['w'][d] * v[2] - 0.5 * z['w'][d] * 1.25 / v[3]
        res8[e] = full(ret2(e, WG3[e], base=base))
    judge('U8_model_as_core_forecast', res8, diagnostic=u8)
else: OUT['U8_model_as_core_forecast'] = dict(diagnostic=u8, adopt_candidate=False, note='rule not unlocked')

# ---------------------------------------------------------------- U9: plumbing calendar
def nth_sunday(y, m, n): d0 = dt.date(y, m, 1); return d0 + dt.timedelta(days=(6 - d0.weekday()) % 7 + 7 * (n - 1))
def last_sunday(y, m): d0 = dt.date(y, m + 1, 1) - dt.timedelta(days=1); return d0 - dt.timedelta(days=(d0.weekday() + 1) % 7)
def third_friday(y, m): d0 = dt.date(y, m, 1); return d0 + dt.timedelta(days=(4 - d0.weekday()) % 7 + 14)
def second_thursday(y, m): d0 = dt.date(y, m, 1); return d0 + dt.timedelta(days=(3 - d0.weekday()) % 7 + 7)
ALLD = sorted({d for e in ERAS for d in E[e]['z']['dl']}); FL = {k: set() for k in ('clock_mismatch', 'vix_settlement', 'quarter_end', 'roll_week', 'after_holiday')}
for y in range(2010, 2027):
    a, b = nth_sunday(y, 3, 2), last_sunday(y, 3); c_, d_ = last_sunday(y, 10), nth_sunday(y, 11, 1)
    FL['clock_mismatch'] |= {x for x in ALLD if a.isoformat() <= x < b.isoformat() or c_.isoformat() <= x < d_.isoformat()}
    for m in range(1, 13):
        ny, nm = (y, m + 1) if m < 12 else (y + 1, 1); FL['vix_settlement'].add((third_friday(ny, nm) - dt.timedelta(days=30)).isoformat())
    for m in (3, 6, 9, 12):
        th = second_thursday(y, m); mon = th - dt.timedelta(days=3); FL['roll_week'] |= {(mon + dt.timedelta(days=k)).isoformat() for k in range(5)}
for e in ERAS:
    dl = E[e]['z']['dl']
    for p, d in zip(dl, dl[1:]):
        g = (dt.date.fromisoformat(d) - dt.date.fromisoformat(p)).days; wd_ = dt.date.fromisoformat(d).weekday()
        if g > 1 and not (g == 3 and wd_ == 0): FL['after_holiday'].add(d)
        if p[:7] != d[:7] and p[5:7] in ('03', '06', '09', '12'): FL['quarter_end'].add(p)
kept = collections.defaultdict(list)
for r in rows:
    if G3.get(r['id']) == 1.0: kept[r['date']].append(FR[r['id']][0])
KD = sorted(kept); ks = np.array([sum(kept[d]) for d in KD]); kn = np.array([len(kept[d]) for d in KD]); ky = np.array([int(d[:4]) for d in KD]); kera = np.array([d < '2021' for d in KD])
def diff(fl, m=None):
    m = np.ones(len(KD), bool) if m is None else m; a = fl & m; b = (~fl) & m
    return ks[a].sum() / max(1, kn[a].sum()) - ks[b].sum() / max(1, kn[b].sum())
u9 = {}; unlocked9 = []
for name, S in FL.items():
    fl = np.array([d in S for d in KD]); obs = diff(fl); cnt = 0; yidx = [np.where(ky == y)[0] for y in sorted(set(ky))]
    for _ in range(10000):
        sh = fl.copy()
        for ix in yidx: sh[ix] = fl[rng.permutation(ix)]
        cnt += abs(diff(sh)) >= abs(obs)
    u9[name] = dict(flag_days_with_trades=int(fl.sum()), trades=int(kn[fl].sum()), avg_free_R_flag=round(float(ks[fl].sum() / max(1, kn[fl].sum())), 3), avg_free_R_other=round(float(ks[~fl].sum() / kn[~fl].sum()), 3),
                    diff_2010_20=round(float(diff(fl, kera)), 3), diff_2021_26=round(float(diff(fl, ~kera)), 3), p_pooled=round(cnt / 10000, 4))
    u9[name]['unlocked'] = bool(u9[name]['p_pooled'] < 0.01 and u9[name]['diff_2010_20'] < 0 and u9[name]['diff_2021_26'] < 0)
    if u9[name]['unlocked']: unlocked9.append(name)
    print('U9', name, u9[name], flush=True)
OUT['U9_plumbing_calendar'] = dict(flags=u9, adopt_candidate=False)
for name in unlocked9:
    G9 = {t['id']: (0.0 if t['date'] in FL[name] else G3.get(t['id'], 1.0)) for e in ERAS for k, t in enumerate(Q[e]['tr']) if Q[e]['mom'][k]}
    w = wfast(G9); judge('U9_skip_' + name, {e: full(ret2(e, w[e])) for e in ERAS})

# ---------------------------------------------------------------- U10: news-candle trades
X26 = f'{A}/_cache/ext26'
def rid(r): return set(re.findall(r'(20[0-2]\d-\d\d-\d\d)', open(f'{X26}/rid{r}.dates').read()))
R830 = rid(10) | rid(50) | rid(46) | rid(9) | rid(53)
def news_trade(e, d):
    B = C29[e]['pm'].get(d); TK = C29[e]['sl']
    if not B: return None
    cndl = [b for b in B if 510 <= b[0] <= 514]; rest = [b for b in B if 515 <= b[0] <= 564]
    if len(cndl) < 4 or cndl[-1][0] != 514 or len(rest) < 30: return None
    o, c_ = cndl[0][1], cndl[-1][4]; hi = max(b[2] for b in cndl); lo = min(b[3] for b in cndl)
    if c_ == o: return None
    s = 1 if c_ > o else -1; entry = c_ + s * 4 * TK; stop = lo if s == 1 else hi; risk_pts = (entry - stop) * s
    if risk_pts <= 0: return None
    px = None
    for b in rest:
        if (b[3] <= stop) if s == 1 else (b[2] >= stop): px = stop - s * 2 * TK; break
    if px is None: px = rest[-1][4] - s * 2 * TK
    return dict(date=d, side=s, risk_pts=risk_pts, gross=(px - entry) * s / risk_pts, cost=2 * C29[e]['cost'] / risk_pts, range_pts=hi - lo)
NT = {e: [t for t in (news_trade(e, d) for d in E[e]['days']) if t] for e in ERAS}; u10 = {}
for e in ERAS:
    tk = [t for t in NT[e] if t['cost'] <= CAP]; rel = [t['gross'] - t['cost'] for t in tk if t['date'] in R830]; plc = [t['gross'] - t['cost'] for t in tk if t['date'] not in R830]
    relg = [t['gross'] for t in tk if t['date'] in R830]
    u10[e] = dict(release_days_in_era=sum(1 for d in E[e]['days'] if d in R830), release_trades=len(rel), release_avg_net_R=round(float(np.mean(rel)), 3) if rel else None, release_avg_gross_R=round(float(np.mean(relg)), 3) if rel else None,
                  release_win_rate=round(float(np.mean([x > 0 for x in rel])), 3) if rel else None, release_total_net_R=round(float(np.sum(rel)), 1),
                  placebo_trades=len(plc), placebo_avg_net_R=round(float(np.mean(plc)), 3) if plc else None, cost_rule_removed_share_release=round(1 - len(rel) / max(1, sum(1 for t in NT[e] if t['date'] in R830)), 3))
al = [(t['date'][:4], t['date'] in R830, t['gross'] - t['cost']) for e in ERAS for t in NT[e] if t['cost'] <= CAP]
yy = np.array([a for a, _, _ in al]); ff = np.array([b for _, b, _ in al]); xx = np.array([c_ for _, _, c_ in al]); obs = xx[ff].mean() - xx[~ff].mean(); cnt = 0; yidx = [np.where(yy == y)[0] for y in sorted(set(yy))]
for _ in range(10000):
    sh = ff.copy()
    for ix in yidx: sh[ix] = ff[rng.permutation(ix)]
    cnt += (xx[sh].mean() - xx[~sh].mean()) >= obs
u10['release_minus_placebo_avg_net_R'] = round(float(obs), 3); u10['p_one_sided'] = round(cnt / 10000, 4)
m1 = all((u10[e]['release_avg_net_R'] or -1) > 0 for e in ERAS) and u10['p_one_sided'] < 0.05; u10['mark1_pass'] = bool(m1)
res10 = {}
for e in ERAS:
    di = {d: k for k, d in enumerate(E[e]['days'])}; x = np.zeros(Q[e]['nd'])
    for t in NT[e]:
        if t['cost'] <= CAP and t['date'] in R830: x[di[t['date']]] += t['gross'] - t['cost']
    res10[e] = full(ret2(e, WG3[e], extra=x))
print('U10', u10, flush=True); ok10 = judge('U10_news_candle_trades', res10, diagnostic=u10); OUT['U10_news_candle_trades']['adopt_candidate'] = bool(m1 and ok10)

json.dump(OUT, open(f'{A}/batch29.json', 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
print('ADOPT CANDIDATES:', [k for k, v in OUT.items() if isinstance(v, dict) and v.get('adopt_candidate')] or 'none')
