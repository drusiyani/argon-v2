"""Batch 41: three social-media strategies made mechanical (rules: analysis/BATCH41_PREREG.md)."""
import os, sys, json, math, collections, statistics as stt
A = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(A)
sys.path.insert(0, A); sys.path.insert(0, os.path.join(ROOT, 'research')); sys.path.insert(0, os.path.join(ROOT, 'engine'))
import common as c
from batch38 import rules_daily, stats
ERA = c.DATA; RISK = 0.5; COSTPTS = 1.1; CAP = 0.10

def index_by_day(s):
    T, O, H, L, C, n, mins, days, wd = c.prep(s); idx = collections.defaultdict(list)
    for i in range(n): idx[days[i]].append(i)
    return (O, H, L, C, mins), idx

def bars5(P, ids, m0, m1):
    O, H, L, Cc, mins = P; b = collections.OrderedDict()
    for i in ids:
        m = mins[i]
        if m0 <= m < m1:
            k = m - m % 5
            if k not in b: b[k] = [O[i], H[i], L[i], Cc[i]]
            else: x = b[k]; x[1] = max(x[1], H[i]); x[2] = min(x[2], L[i]); x[3] = Cc[i]
    return list(b.items())

def manage(P, ids, start_min, side, entry, stop, target, deadline=None, market=False):
    """Walk 1-minute bars from start_min. Returns gross R (None if never filled before deadline)."""
    O, H, L, Cc, mins = P; risk = abs(entry - stop); filled = False
    for i in ids:
        m = mins[i]
        if m < start_min: continue
        if not filled:
            if deadline and m >= deadline: return None
            if m >= 955: return None
            if market or (side == 1 and L[i] <= entry) or (side == -1 and H[i] >= entry):
                entry = O[i] if market else (min(entry, O[i]) if side == 1 else max(entry, O[i])); filled = True; risk = abs(entry - stop)
                if risk <= 0: return None
            else: continue
        if m >= 955: return side * (O[i] - entry) / risk
        if (side == 1 and L[i] <= stop) or (side == -1 and H[i] >= stop): return side * (stop - entry) / risk
        if (side == 1 and H[i] >= target) or (side == -1 and L[i] <= target): return side * (target - entry) / risk
    return None

def s_smc(P, ids):
    b = bars5(P, ids, 480, 955); hs = [x[1][1] for x in b]; ls = [x[1][2] for x in b]; cs = [x[1][3] for x in b]; ms = [x[0] for x in b]
    sh = sl = None
    for i in range(len(b)):
        j = i - 2
        if j >= 2 and i < len(b):
            if hs[j] > max(hs[j - 2:j] + hs[j + 1:i + 1]): sh = hs[j]
            if ls[j] < min(ls[j - 2:j] + ls[j + 1:i + 1]): sl = ls[j]
        if not (570 <= ms[i] < 720) or i < 2 or sh is None or sl is None: continue
        if cs[i] > sh and ls[i] > hs[i - 2]:
            e = (ls[i] + hs[i - 2]) / 2; st = sl
            if e > st: return 1, e, st, e + 1.5 * (e - st), ms[i] + 5, ms[i] + 65
            sh = None
        if cs[i] < sl and hs[i] < ls[i - 2]:
            e = (hs[i] + ls[i - 2]) / 2; st = sh
            if e < st: return -1, e, st, e - 1.5 * (st - e), ms[i] + 5, ms[i] + 65
            sl = None
    return None

def twap(P, ids):
    O, H, L, Cc, mins = P; xs = [(H[i] + L[i] + Cc[i]) / 3 for i in ids if 570 <= mins[i] < 960]
    return sum(xs) / len(xs) if xs else None

def s_vwap(P, ids, pv, Pe, ide):
    if pv is None: return None
    b = bars5(P, ids, 570, 955); be = dict(bars5(Pe, ide, 570, 955))
    if not b or 570 not in be: return None
    q0 = b[0][1][0]; e0 = be[570][0]
    for m, (o, h, l, cl) in b:
        if not (585 <= m < 690): continue
        if m not in be: continue
        rel = (cl / q0 - 1) - (be[m][3] / e0 - 1)
        if l < pv < h:
            if o < pv and cl < pv and rel < 0: return -1, cl, h, cl - 2 * (h - cl), m + 5, 'market'
            if o > pv and cl > pv and rel > 0: return 1, cl, l, cl + 2 * (cl - l), m + 5, 'market'
    return None

def s_sweep(P, ids, prev_ids, atr_kind):
    O, H, L, Cc, mins = P
    a = [i for i in ids if 120 <= mins[i] < 360]; bb = [i for i in ids if 360 <= mins[i] < 600]
    if len(a) < 120 or len(bb) < 120: return None
    ah, al = max(H[i] for i in a), min(L[i] for i in a); bh, bl = max(H[i] for i in bb), min(L[i] for i in bb); bc = Cc[bb[-1]]
    side = 1 if (bl < al and bc > ah) else -1 if (bh > ah and bc < al) else 0
    if not side: return None
    hist = prev_ids + [i for i in ids if mins[i] < 600]
    step = 5 if atr_kind == '5m' else 60
    blocks = [hist[k:k + step] for k in range(len(hist) - 14 * step, len(hist), step)] if len(hist) >= 14 * step else []
    if len(blocks) < 14: return None
    atr = sum(max(H[i] for i in g) - min(L[i] for i in g) for g in blocks) / 14
    mid = (bh + bl) / 2
    return side, mid, mid - side * 4 * atr, mid + side * 2 * atr, 600, None

def main():
    P, idx = index_by_day('NQ'); Pe, ide = index_by_day('ES'); R = c.roll('NQ') | c.roll('ES')
    D, dl, _ = c.daily('NQ'); rd = rules_daily()
    names = ['SMC break + FVG', 'prior-day VWAP rejection', '4H sweep (ATR 5m)', '4H sweep (ATR 1h)']
    trades = {k: [] for k in names}; daily = {k: {} for k in names}
    for k in range(1, len(dl)):
        d, p = dl[k], dl[k - 1]
        if d in R or p in R: continue
        ids = idx.get(d, []); 
        if not ids: continue
        sig = {'SMC break + FVG': s_smc(P, ids),
               'prior-day VWAP rejection': s_vwap(P, ids, twap(P, idx.get(p, [])), Pe, ide.get(d, [])),
               '4H sweep (ATR 5m)': s_sweep(P, ids, idx.get(p, []), '5m'), '4H sweep (ATR 1h)': s_sweep(P, ids, idx.get(p, []), '1h')}
        for name, s in sig.items():
            if not s: continue
            side, e, st, tg, start, dead = s; risk = abs(e - st)
            if risk <= 0: continue
            cost = COSTPTS / risk
            if cost > CAP: continue
            mk = dead == 'market'; g = manage(P, ids, start, side, e, st, tg, None if mk else dead, market=mk)
            if g is None: continue
            net = g - cost; trades[name].append(net); daily[name][d] = RISK * net / 100
    days = [d for d in dl[1:] if d not in R]
    book = [rd.get(d, 0.0) for d in days]
    out = dict(era=ERA, period=[days[0], days[-1]], rules_only=stats(book), strategies={})
    for name in names:
        t = trades[name]; x = [daily[name].get(d, 0.0) for d in days]
        sd = stt.pstdev(x)
        out['strategies'][name] = dict(trades=len(t), win_rate=round(sum(1 for v in t if v > 0) / len(t), 3) if t else None,
            avg_R=round(stt.mean(t), 3) if t else None, total_R=round(sum(t), 1),
            own_sharpe=round(stt.mean(x) / sd * math.sqrt(252), 3) if sd else 0,
            rules_with_it=stats([a + b for a, b in zip(book, x)]))
        print(name, out['strategies'][name], flush=True)
    json.dump(out, open(f'{A}/batch41_{ERA}.json', 'w'), indent=1)

if __name__ == '__main__': main()
