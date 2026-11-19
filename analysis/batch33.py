"""Batch 33: Gemini's overconfidence fixes. Rules: analysis/BATCH33_PREREG.md (committed before this file ran)."""
import os, bisect
A = os.path.dirname(os.path.abspath(__file__)); s29 = open(f'{A}/batch29.py').read(); BAR = '# ---------------------------------------------------------------- '
exec(s29.split(BAR + 'U1')[0]); OUT = collections.OrderedDict(G3=REF)
src = open(f'{A}/batch14.py').read(); i = src.index('NAMES = ['); K = eval(src[i + 8:src.index(']', i) + 1]).index('yesterday rules R')
SUB = (('2010-13', '2010', '2014'), ('2014-17', '2014', '2018'), ('2018-20', '2018', '2021'), ('2021-25', '2021', '2026'), ('2026', '2026', '2027'))
def sub(G):
    w = wfast(G); out = {}
    for lab, a, b in SUB:
        e = 'lockbox2010' if a < '2021' else 'databento'; m = np.array([a <= d < b for d in E[e]['days']]); out[lab] = round(cagr(ret2(e, w[e])[m]), 1)
    return out
def july(G):
    e = 'databento'; r = ret2(e, wfast(G)[e] * 1.25); ix = np.array([d.startswith('2026-07') for d in E[e]['days']]); return round(100 * (float(np.prod(1 + r[ix])) - 1), 1)
S3 = sub(G3)
def test(name, G):
    w = wfast(G); res = {e: full(ret2(e, w[e])) for e in ERAS}; judge(name, res, luck(G)); s = sub(G); lvl = sum(s[k] >= S3[k] - 0.1 for k in S3); r = OUT[name]
    r.update(sub_periods=dict(G3=S3, idea=s, level_or_better=int(lvl)), july_2026_at_0625=dict(G3=july(G3), idea=july(G)), changed_share=round(float(np.mean([G[i] != G3[i] for i in G3])), 3))
    r['clears_noise_floor'] = bool(res['databento']['cagr_pct'] - REF['databento']['cagr_pct'] >= 3 and res['lockbox2010']['cagr_pct'] - REF['lockbox2010']['cagr_pct'] >= 1.5)
    r['adopt'] = bool(r['adopt_candidate'] and r['clears_noise_floor'] and lvl >= 4); print(name, {k: r[k] for k in ('sub_periods', 'july_2026_at_0625', 'changed_share', 'clears_noise_floor', 'adopt')}, flush=True)
# H1
def h1(r): f = list(r['f']); f[K] = max(f[K], 0.0); return f
G1, _ = pipeline(feat=h1); test('H1_hinged_yesterday_R', G1)
# H2 variance ratio
def dayvr(B):
    cl = {b[0]: b[4] for b in B if 570 <= b[0] <= 959}; o = [b[1] for b in B if b[0] >= 570]
    if len(cl) < 300 or not o: return None
    def marks(step):
        out = [o[0]]; last = o[0]
        for m in range(569 + step, 960, step):
            c = None
            for mm in range(m, m - step, -1):
                if mm in cl: c = cl[mm]; break
            last = c if c is not None else last; out.append(last)
        x = np.log(np.array(out)); return float((np.diff(x) ** 2).sum())
    return marks(30), marks(5)
VRD = {}
for e in ERAS:
    ds = sorted(C29[e]['m1']); per = {d: dayvr(C29[e]['m1'][d]) for d in ds}; ok = [d for d in ds if per[d]]
    for d in sorted({r['date'] for r in rows if r['id'][0] == e}):
        j = bisect.bisect_left(ok, d); win = ok[max(0, j - 20):j]
        if len(win) < 10: VRD[d] = 0.0; continue
        a = sum(per[x][0] for x in win); b = sum(per[x][1] for x in win); VRD[d] = math.log(a / (6 * b)) if a > 0 and b > 0 else 0.0
vv = np.array([VRD[r['date']] for r in rows]); print('ln VR mean', round(float(vv.mean()), 3), 'sd', round(float(vv.std()), 3), 'July 2026', round(float(np.mean([VRD[r['date']] for r in rows if r['date'].startswith('2026-07')])), 3), flush=True)
G2, _ = pipeline(feat=lambda r: list(r['f']) + [VRD[r['date']]]); test('H2_variance_ratio_feature', G2)
json.dump(OUT, open(f'{A}/batch33.json', 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
