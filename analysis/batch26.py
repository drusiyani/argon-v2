"""Batch 26 (15 Nov 2026). Rules and marks: analysis/BATCH26_PREREG.md (committed before this file ran).
Needs the batch 14 / 24 caches and analysis/_cache/ext26/ (ALFRED release dates, SEC filings; see the pre-registration)."""
import os, json, re, datetime as dt, math
from zoneinfo import ZoneInfo
from scipy import stats as sst
A = os.path.dirname(os.path.abspath(__file__))
src24 = open(f'{A}/batch24.py').read()
exec(src24.split('# ---- vectorised package returns per era')[0])
exec(src24.split('# ---- vectorised package returns per era')[1].split('ELIG = {')[0])
NY = ZoneInfo('America/New_York'); X = f'{A}/_cache/ext26'
# ---------- calendar
TD = sorted(set(d for e in ERAS for d in E[e]['z']['dl'])); TDi = {d: i for i, d in enumerate(TD)}
def rid(r): return set(re.findall(r'(20[0-2]\d-\d\d-\d\d)', open(f'{X}/rid{r}.dates').read()))
R830 = rid(10) | rid(50) | rid(46) | rid(9) | rid(53); JOLTS = rid(192)
ISM = set()
for ym in sorted({d[:7] for d in TD}):
    m = [d for d in TD if d[:7] == ym]
    if m: ISM.add(m[0])
    if len(m) >= 3: ISM.add(m[2])
TIER1 = R830 | JOLTS | ISM; TEN = JOLTS | ISM
# ---------- SEC: top 8 by public float, item 2.02 filing times
SEC = json.load(open(f'{X}/sec.json'))
def top8(year):
    cut = f'{year}-01-01'; v = {}
    for tk, x in SEC.items():
        fl = [f for f in x['float'] if f[0] < cut and f[1] > 0]
        if fl: v[tk] = max(fl)[1] if False else sorted(fl)[-1][1]
    return set(sorted(v, key=lambda k: -v[k])[:8])
TOP = {y: top8(y) for y in range(2010, 2027)}
EARN = []
for tk, x in SEC.items():
    for a in x['e8']:
        t = dt.datetime.fromisoformat(a.replace('Z', '+00:00')).astimezone(NY); EARN.append((tk, t))
def after_close_on(d, tks):   # filings after 16:00 ET on trading day d and before 09:30 on the next trading day
    i = TDi[d]
    if i + 1 >= len(TD): return set()
    lo = dt.datetime.fromisoformat(d + 'T16:00').replace(tzinfo=NY); hi = dt.datetime.fromisoformat(TD[i + 1] + 'T09:30').replace(tzinfo=NY)
    return {tk for tk, t in EARN if tk in tks and lo <= t < hi}
MEGA, FREEZE = {}, {}
for i, d in enumerate(TD):
    if i == 0 or i + 2 >= len(TD): continue
    tks = TOP.get(int(d[:4]), set()); MEGA[d] = bool(after_close_on(TD[i - 1], tks))
    FREEZE[d] = (not MEGA[d]) and (d not in TIER1) and len(after_close_on(d, tks) | after_close_on(TD[i + 1], tks)) >= 2
# ---------- G3 rank and net edge in sequence
RANK, NET, MEDNET = {}, {}, {}; hp, hn = [], []
for r in rows:
    if r['id'] not in PRED: continue
    p = PRED[r['id']]; n_ = p - 1.25 / FR[r['id']][1]
    RANK[r['id']] = (float(np.mean(np.array(hp[-252:]) < p)) if len(hp) >= 100 else None); MEDNET[r['id']] = (float(np.median(hn[-252:])) if len(hn) >= 100 else None)
    NET[r['id']] = n_; hp.append(p); hn.append(n_)
TR = {t['id']: t for e in ERAS for t in E[e]['tr']}
def s1(i): return FREEZE.get(TR[i]['date'], False) and RANK.get(i) is not None and RANK[i] < 0.667
def s2(i): t = TR[i]; d = t['date']; return t['strat'] == 'quantlab' and d in TEN and d not in R830 and MEDNET.get(i) is not None and NET[i] < MEDNET[i]
def on_top(f): return {i: (0.0 if (m == 0.0 or f(i)) else 1.0) for i, m in G3.items()}
S1, S2 = on_top(s1), on_top(s2)
# ---------- kill switches (paper-track all G3-kept trades, in time order)
kept = sorted([TR[i] for i, m in G3.items() if m == 1.0], key=lambda t: (t['date'], t['entry_min'])); kid = [t['id'] for t in kept]; kr = np.array([net(t) for t in kept])
kyear = [t['date'][:4] for t in kept]
def k1():
    W = {}; C = 0.0; w = 1.0
    for j, t in enumerate(kept):
        prior = kr[[q for q in range(j) if kyear[q] < kyear[j]]] if j else np.array([])
        W[kid[j]] = w if len(prior) >= 200 else 1.0
        if len(prior) >= 200:
            mu0, s0 = prior.mean(), prior.std(); z = (kr[j] - mu0) / s0; C = min(8.03, max(0.0, C - z - 0.25))
            if w == 1.0 and C >= 4.0: w = 0.5
            if w > 0 and C >= 8.03: w = 0.0
            if w == 0.0 and C < 4.015: w = 0.5
            if w == 0.5 and C <= 0.0: w = 1.0
    return W
def k2():
    dR = collections.defaultdict(float)
    for j, t in enumerate(kept): dR[t['date']] += kr[j]
    days = [d for d in TD if d >= kept[0]['date']]; x = np.array([dR.get(d, 0.0) for d in days]); wday = {}; w = 1.0
    def psr(v):
        sd = v.std()
        if sd == 0: return 0.5
        sr = v.mean() / sd; g3 = sst.skew(v); g4 = sst.kurtosis(v, fisher=False); den = 1 - g3 * sr + (g4 - 1) / 4 * sr * sr
        return float(sst.norm.cdf(sr * math.sqrt(len(v) - 1) / math.sqrt(max(den, 1e-9))))
    for k, d in enumerate(days):
        wday[d] = w
        if k + 1 >= 252:
            p252 = psr(x[k - 251:k + 1]); p126 = psr(x[k - 125:k + 1])
            if w == 0.0: w = 0.5 if (p252 >= 0.5 or p126 >= 0.85) else 0.0
            else: w = 1.0 if p252 >= 0.8 else (0.5 if p252 >= 0.5 else 0.0)
    return {kid[j]: wday.get(t['date'], 1.0) for j, t in enumerate(kept)}, wday
def k3():
    H = 1 / 150; mu = np.array([0.0]); ka = np.array([1.0]); al = np.array([1.0]); be = np.array([1.0]); P = np.array([1.0]); W = {}; w = 1.0
    for j, t in enumerate(kept):
        W[kid[j]] = w; x = kr[j]
        scale = np.sqrt(be * (ka + 1) / (al * ka)); pred = sst.t.pdf(x, 2 * al, loc=mu, scale=scale)
        grow = P * pred * (1 - H); cp = (P * pred * H).sum(); P = np.r_[cp, grow]; P = P / P.sum()
        mu_n = (ka * mu + x) / (ka + 1); ka_n = ka + 1; al_n = al + 0.5; be_n = be + ka * (x - mu) ** 2 / (2 * (ka + 1))
        mu = np.r_[0.0, mu_n]; ka = np.r_[1.0, ka_n]; al = np.r_[1.0, al_n]; be = np.r_[1.0, be_n]
        if len(P) > 1500: P, mu, ka, al, be = P[:1500] / P[:1500].sum(), mu[:1500], ka[:1500], al[:1500], be[:1500]
        pm = float((P * (1 - sst.t.cdf(0, 2 * al, loc=mu, scale=np.sqrt(be / (al * ka))))).sum())
        if pm < 0.50: w = 0.0
        elif w == 1.0 and pm < 0.75: w = 0.5
        elif w < 1.0 and pm >= 0.80: w = 1.0
        elif w == 0.0 and pm >= 0.65: w = 0.5
    return W, pm
K1 = k1(); K2, K2day = k2(); K3, K3last = k3()
def weighted(Wk): return {i: (m * Wk.get(i, 1.0)) for i, m in G3.items()}
# ---------- scoring
REF = {e: full(ret(e, wvec(e, G3))) for e in ERAS}; rng = np.random.default_rng(20261117); N = 5000
def extra_luck(M):
    grp = {e: [] for e in ERAS}; base_w = {e: wvec(e, G3) for e in ERAS}; tgt = {e: cagr(ret(e, wvec(e, M))) for e in ERAS}
    for e in ERAS:
        tr = Q[e]['tr']; kp = np.array([t['id'] in G3 and G3[t['id']] == 1.0 for t in tr]); ex = np.array([kp[i] and M.get(t['id'], 1.0) == 0.0 for i, t in enumerate(tr)])
        for y in sorted(set(Q[e]['yr'])):
            idx = np.where(kp & (Q[e]['yr'] == y))[0]; k = int(ex[idx].sum())
            if k: grp[e].append((idx, k))
    hits = 0
    for _ in range(N):
        ok = True
        for e in ERAS:
            w = base_w[e].copy()
            for idx, k in grp[e]: w[rng.choice(idx, k, replace=False)] = 0.0
            ok &= cagr(ret(e, w)) >= tgt[e]
        hits += ok
    return int(hits)
SUB = (('2010-13', 'lockbox2010', '2010', '2014'), ('2014-17', 'lockbox2010', '2014', '2018'), ('2018-20', 'lockbox2010', '2018', '2021'), ('2021-25', 'databento', '2021', '2026'), ('2026', 'databento', '2026', '2027'))
def subs(M):
    out = {}
    for lab, e, a, b in SUB:
        x = ret(e, wvec(e, M)); seg = [v for v, d in zip(x, E[e]['days']) if a <= d < b]; m = metrics(seg); out[lab] = f"{m['cagr_pct']:+.1f}% / {m['worst_drop_pct']:.1f}%"
    return out
RES = collections.OrderedDict(); RES['G3 (reference)'] = dict(result=REF, sub=subs(G3))
for nm, M in (('S1 mega-cap pre-earnings freeze', S1), ('S2 10:00 release collision', S2)):
    h = {e: full(ret(e, wvec(e, M))) for e in ERAS}; st_ = all(strict(h[e], REF[e]) for e in ERAS); lk = extra_luck(M)
    extra = {lab: int(sum(1 for i, m in M.items() if m == 0.0 and G3[i] == 1.0 and a <= TR[i]['date'] < b)) for lab, _, a, b in SUB}
    rem = {lab: (lambda v: round(float(np.mean(v)), 3) if v else None)([net(TR[i]) for i, m in M.items() if m == 0.0 and G3[i] == 1.0 and a <= TR[i]['date'] < b]) for lab, _, a, b in SUB}
    RES[nm] = dict(result=h, strict_vs_G3=bool(st_), luck_random_beating_both_eras=lk, adopt_candidate=bool(st_ and lk / N < 0.05), extra_skips=extra, extra_skipped_avg_R=rem, sub=subs(M))
for nm, Wk, last in (('K1 CUSUM', K1, None), ('K2 rolling PSR', K2, None), ('K3 Bayesian changepoint', K3, K3last)):
    M = weighted(Wk); h = {e: full(ret(e, wvec(e, M))) for e in ERAS}; st_ = all(strict(h[e], REF[e]) for e in ERAS)
    share = {lab: {str(w): round(float(np.mean([Wk[i] == w for i in kid if a <= TR[i]['date'] < b])), 3) for w in (1.0, 0.5, 0.0)} for lab, _, a, b in SUB}
    now = Wk[kid[-1]]
    RES[nm] = dict(result=h, strict_vs_G3=bool(st_), adopt_candidate=bool(st_), weight_share=share, weight_on_last_trade=now, sub=subs(M))
RES['K2 rolling PSR']['weight_for_13_Nov_2026'] = K2day.get(TD[-1]); RES['K3 Bayesian changepoint']['final_P_mu_positive'] = round(K3last, 3)
# ---------- diagnostics
calib = {}
for y in sorted({TR[i]['date'][:4] for i in G3}):
    ks = [i for i, m in G3.items() if m == 1.0 and TR[i]['date'][:4] == y]
    if ks: calib[y] = dict(kept=len(ks), avg_prediction=round(float(np.mean([PRED[i] for i in ks])), 3), avg_friction_free_R=round(float(np.mean([FR[i][0] for i in ks])), 3), avg_net_R=round(float(np.mean([net(TR[i]) for i in ks])), 3))
counts = dict(freeze_days=sum(FREEZE.values()), mega_days=sum(MEGA.values()), ten_oclock_days=len([d for d in TD if d in TEN and d not in R830]), top8_by_year={y: sorted(v) for y, v in TOP.items()})
json.dump(dict(results=RES, calibration_by_year=calib, counts=counts), open(f'{A}/batch26.json', 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
fmt = lambda h: f"{h['cagr_pct']:5.1f} {h['sortino']:4.2f} {h['worst_drop_pct']:6.1f} {h['boot']:5.1f}"
for nm, r in RES.items():
    print(f"{nm:34s}", ' | '.join(fmt(r['result'][e]) for e in ERAS), '| strict', r.get('strict_vs_G3'), 'luck', r.get('luck_random_beating_both_eras'), 'ADOPT' if r.get('adopt_candidate') else '')
    print('    sub', r['sub']); [print('   ', k, r[k]) for k in ('extra_skips', 'extra_skipped_avg_R', 'weight_share', 'weight_on_last_trade', 'weight_for_13_Nov_2026', 'final_P_mu_positive') if k in r]
print('counts', {k: v for k, v in counts.items() if k != 'top8_by_year'}); print('top8', {y: counts['top8_by_year'][y] for y in (2011, 2016, 2021, 2026)})
for y, v in calib.items(): print('calib', y, v)
