"""Two strategies from @thequantbuilder's videos, rules and pass marks committed BEFORE running (30 Oct 2026).
All NQ/ES data has been seen before, so this is in-sample; it is scored on both eras so a one-regime fluke can't pass.

A. WIDENED NOISE BAND: Argon's noise band with wider bands only, MULTS=(2.0,) (Argon uses 1.0 and 1.5), same walk-forward over
   30/60-minute checks and band/VWAP stops. Nearby: (1.75,) and (2.5,).
   Replaces Argon's noise band only if: positive net R in 2011-2017 AND 2018-2026; Sharpe at least +0.10 above the current noise
   band in both eras; positive at double costs; both nearby settings positive.
B. TJR'S STRATEGY (as coded from the video):
   - 9:30-11:00 New York: NQ sweeps its pre-market (4:00-9:30) high (a SHORT setup) or low (a LONG setup).
   - FVG flip on 5-minute candles after the sweep: for a short, a close below the bottom of the latest bullish gap (low[k] > high[k-2])
     formed since 9:30; for a long, a close above the top of the latest bearish gap.
   - Agreement: ES has swept the same side and flipped the same way within 15 minutes before or at NQ's flip.
   - 1-minute break: the first NQ 1-minute close beyond the extreme of the previous 5 one-minute candles, by 11:30. Enter next minute + 1 tick.
   - Stop 1 tick beyond the sweep extreme (day's high/low so far). Target 2R, limit, must trade 1 tick through. Flat 15:55 (FOMC early).
   - One trade a day. Costs as always. Nearby: target 1.5R and 3R.
   Counts as working only if: positive net R in both eras; positive at double costs; both nearby settings positive.
   Claimed in the video: 64% win rate."""
import os, sys, json, collections, statistics as stt
os.environ['ARGON_FULL'] = '1'; HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)

def day_index(c, s):
    T, O, H, L, C, n, mins, days, wd = c.prep(s); idx = collections.defaultdict(list)
    for i in range(n):
        if 240 <= mins[i] < 960: idx[days[i]].append(i)
    return idx

def flips(c, s, d, idx):
    """Sweep side and flip time for one symbol on one day: returns {side: (flip_minute, sweep_extreme)}."""
    T, O, H, L, C, n, mins, days, wd = c.prep(s); r = idx.get(d, [])
    pm = [i for i in r if 240 <= mins[i] < 570]; rth = [i for i in r if 570 <= mins[i] < 960]
    if len(pm) < 60 or len(rth) < 300: return {}
    ph, pl = max(H[i] for i in pm), min(L[i] for i in pm)
    b5 = collections.OrderedDict()
    for i in rth:
        k = mins[i] // 5 * 5
        if k not in b5: b5[k] = [k, H[i], L[i], C[i], i]
        else: b = b5[k]; b[1] = max(b[1], H[i]); b[2] = min(b[2], L[i]); b[3] = C[i]
    bars = list(b5.values()); out = {}
    for side in (-1, 1):                    # -1: swept the high, look to sell; +1: swept the low, look to buy
        sweep = next((m for m, h, l, cc, i in bars if m <= 655 and ((h > ph) if side == -1 else (l < pl))), None)
        if sweep is None: continue
        gap = None; ext = None
        for k, (m, h, l, cc, i) in enumerate(bars):
            if m > 660: break
            ext = (max(ext or h, h) if side == -1 else min(ext or l, l)) if m >= sweep else ext
            if k >= 2:
                if side == -1 and l > bars[k - 2][1]: gap = (bars[k - 2][1], l)        # bullish gap: bottom, top
                if side == 1 and h < bars[k - 2][2]: gap = (h, bars[k - 2][2])          # bearish gap: bottom, top
            if m >= sweep and gap and ((cc < gap[0]) if side == -1 else (cc > gap[1])):
                out[side] = (m + 4, ext); break
    return out

def tjr(c, target=2.0):
    s = 'NQ'; P = c.prep(s); T, O, H, L, C, n, mins, days, wd = P; TK = c.SL[s]; out = []
    ni, ei = day_index(c, 'NQ'), day_index(c, 'ES'); R = c.roll('NQ')
    for d in sorted(ni):
        if d in R or d in c.bad_days('NQ'): continue
        fn, fe = flips(c, 'NQ', d, ni), flips(c, 'ES', d, ei)
        cands = [(fn[sd][0], sd) for sd in fn if sd in fe and fn[sd][0] - 15 <= fe[sd][0] <= fn[sd][0]]
        if not cands: continue
        t0, side = min(cands); ext = fn[side][1]; rth = [i for i in ni[d] if 570 <= mins[i] < 960]
        ex = c.fexit(d) if d in c.FOMC else 955; entry = None
        for q, i in enumerate(rth):
            if mins[i] <= t0 or q < 5: continue
            if mins[i] > 690: break
            prev = rth[q - 5:q]
            if (C[i] < min(L[x] for x in prev)) if side == -1 else (C[i] > max(H[x] for x in prev)):
                if q + 1 >= len(rth): break
                e = rth[q + 1]; entry = O[e] + side * TK; ext = max(ext, max(H[x] for x in rth[:q + 1] if mins[x] >= 570)) if side == -1 else min(ext, min(L[x] for x in rth[:q + 1] if mins[x] >= 570))
                stop = ext - side * TK * -1 if False else ext + (TK if side == -1 else -TK); risk = (entry - stop) * side
                if risk <= 2 * TK: entry = None; break
                tgt = entry + side * target * risk; res = None
                for x in rth[q + 1:]:
                    if mins[x] >= ex: res = (C[x] - entry) * side; xm = mins[x]; break
                    if (L[x] <= stop) if side == 1 else (H[x] >= stop): res = (stop - side * TK - entry) * side; xm = mins[x]; break
                    if (H[x] >= tgt + TK) if side == 1 else (L[x] <= tgt - TK): res = (tgt - entry) * side; xm = mins[x]; break
                if res is None: res = (C[rth[-1]] - entry) * side; xm = mins[rth[-1]]
                out.append(c.trade('tjr', s, d, 0, side, mins[e], xm, risk, res)); break
    return out

def run():
    import common as c
    res = {}
    def keep(name, t):
        mm1 = collections.defaultdict(float); mm2 = collections.defaultdict(float)
        for x in t: mm1[x['month']] += x['gross'] - x['cost']; mm2[x['month']] += x['gross'] - 2 * x['cost']
        res[name] = dict(n=len(t), m1=dict(mm1), m2=dict(mm2), wins=sum(1 for x in t if x['gross'] - x['cost'] > 0), gross=round(sum(x['gross'] for x in t), 2))
        print(c.DATA, name, len(t), 'trades', round(sum(mm1.values()), 1), 'R', flush=True)
    for name, m in (('nb_now', (1.0, 1.5)), ('nb_wide', (2.0,)), ('nb_wide_lo', (1.75,)), ('nb_wide_hi', (2.5,))):
        keep(name, c.walkforward(c.noiseband('NQ', mults=m)))
    for name, tg in (('tjr', 2.0), ('tjr_1.5', 1.5), ('tjr_3', 3.0)): keep(name, tjr(c, tg))
    json.dump(res, open(f'{c.ROOT}/research/results/tjr_wide_{c.DATA}.json', 'w'))

def judge():
    import common as c
    M = {}
    for f in ('databento', 'lockbox2010'):
        for k, v in json.load(open(f'{c.ROOT}/research/results/tjr_wide_{f}.json')).items():
            x = M.setdefault(k, dict(m1={}, m2={}, n=0, wins=0, gross=0)); x['m1'].update(v['m1']); x['m2'].update(v['m2']); x['n'] += v['n']; x['wins'] += v['wins']; x['gross'] += v['gross']
    A = c.months_between('2011-01', '2017-12'); B = c.months_between('2018-01', '2020-12') + c.months_between('2021-07', '2026-09'); ALL = A + B
    S = lambda k, ms, f='m1': [M[k][f].get(m, 0.0) for m in ms]
    row = lambda k: dict(trades=M[k]['n'], win=round(100 * M[k]['wins'] / max(1, M[k]['n']), 1), R_A=round(sum(S(k, A)), 1), R_B=round(sum(S(k, B)), 1),
                         sh_A=round(c.sharpe(S(k, A)), 2), sh_B=round(c.sharpe(S(k, B)), 2), dbl=round(sum(S(k, ALL, 'm2')), 1), gross=round(M[k]['gross'], 1))
    R = {k: row(k) for k in M}
    w, nb = R['nb_wide'], R['nb_now']
    wide_pass = w['R_A'] > 0 and w['R_B'] > 0 and w['sh_A'] >= nb['sh_A'] + .10 and w['sh_B'] >= nb['sh_B'] + .10 and w['dbl'] > 0 and R['nb_wide_lo']['R_A'] + R['nb_wide_lo']['R_B'] > 0 and R['nb_wide_hi']['R_A'] + R['nb_wide_hi']['R_B'] > 0
    t = R['tjr']; tjr_pass = t['R_A'] > 0 and t['R_B'] > 0 and t['dbl'] > 0 and all(R[k]['R_A'] + R[k]['R_B'] > 0 for k in ('tjr_1.5', 'tjr_3'))
    L = ['# Widened noise band and TJR\'s strategy: results', '', 'Rules and pass marks committed before running. All data had been seen before, so this is in-sample.', '',
         '| | Trades | Win rate | 2011–17 | 2018–26 | Sharpe 2011–17 | Sharpe 2018–26 | Before costs | Double costs |', '|---|---|---|---|---|---|---|---|---|']
    names = dict(nb_now='Noise band now (1×, 1.5×)', nb_wide='Widened noise band (2×)', nb_wide_lo='nearby 1.75×', nb_wide_hi='nearby 2.5×', tjr='TJR (2R target)', **{'tjr_1.5': 'TJR nearby 1.5R', 'tjr_3': 'TJR nearby 3R'})
    for k in ('nb_now', 'nb_wide', 'nb_wide_lo', 'nb_wide_hi', 'tjr', 'tjr_1.5', 'tjr_3'):
        x = R[k]; L.append(f"| {names[k]} | {x['trades']} | {x['win']}% | {x['R_A']:+}R | {x['R_B']:+}R | {x['sh_A']} | {x['sh_B']} | {x['gross']:+}R | {x['dbl']:+}R |")
    L += ['', f"**Widened noise band: {'PASS' if wide_pass else 'FAIL'}.** **TJR: {'PASS' if tjr_pass else 'FAIL'}** (claimed win rate 64%)."]
    open(f'{c.ROOT}/research/results/TJR_WIDEBAND.md', 'w').write('\n'.join(L) + '\n'); json.dump(dict(rows=R, wide_pass=wide_pass, tjr_pass=tjr_pass), open(f'{c.ROOT}/research/results/tjr_wideband.json', 'w'), indent=1)
    print('\n'.join(L))

if __name__ == '__main__':
    run() if sys.argv[1:] == ['run'] else judge()
