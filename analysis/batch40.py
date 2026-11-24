"""Batch 40: five new ideas (rules: analysis/BATCH40_PREREG.md)."""
import os, sys, json, math, csv, bisect, collections, statistics as stt
A = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(A)
sys.path.insert(0, A); sys.path.insert(0, os.path.join(ROOT, 'research')); sys.path.insert(0, os.path.join(ROOT, 'engine'))
import common as c
from batch38 import rules_daily, stats
ERA = c.DATA; COST = {'NQ': 1.1, 'ES': 0.75}

def minute_index(s):
    T, O, H, L, C, n, mins, days, wd = c.prep(s); idx = collections.defaultdict(dict)
    for i in range(n):
        if 570 <= mins[i] < 960: idx[days[i]][mins[i]] = i
    return (O, C), idx

def price(px, idx, d, m, field):
    O, C = px; row = idx.get(d, {})
    if m in row: return (O if field == 'o' else C)[row[m]]
    later = [k for k in row if (k >= m if field == 'o' else k <= m)]
    if not later: return None
    k = min(later) if field == 'o' else max(later)
    return (O if field == 'o' else C)[row[k]]

def sr(x):
    x = [v for v in x]; sd = stt.pstdev(x)
    return round(stt.mean(x) / sd * math.sqrt(252), 3) if sd else 0.0

def main():
    D, dl, _ = c.daily('NQ'); E, el, _ = c.daily('ES'); R = c.roll('NQ') | c.roll('ES')
    pq, iq = minute_index('NQ'); pe, ie = minute_index('ES')
    V = {}
    for row in csv.DictReader(open(os.path.join(ROOT, 'analysis', 'vxn.csv'))):
        try: V[row['date']] = float(row['vxn'])
        except ValueError: pass
    vk = sorted(V); rd = rules_daily(); eset = set(el)
    import datetime as dt
    tradeset = set(dl)
    dsp_hist = []
    rows = collections.defaultdict(list); core_cc = []; core_on = []; days_used = []
    for k in range(260, len(dl)):
        d, p = dl[k], dl[k - 1]; roll = d in R or p in R
        i = bisect.bisect_left(vk, p)
        if i == 0: continue
        v = V[vk[i - 1]]; hist = sorted(V[x] for x in vk[max(0, i - 252):i]); w = min(1.5, hist[len(hist) // 2] / v)
        cc = (D[d]['c'] / D[d]['o'] - 1) if roll else (D[d]['c'] / D[p]['c'] - 1)
        if abs(cc) > 0.15: cc = 0.0
        on = 0.0 if roll else (D[d]['o'] / D[p]['c'] - 1)
        if abs(on) > 0.15: on = 0.0
        core_cc.append(w * cc); core_on.append(w * on); days_used.append(d)
        # 1 last half-hour momentum
        r1 = 0.0
        if not roll:
            a, b = price(pq, iq, d, 570, 'o'), price(pq, iq, d, 599, 'c'); e0, e1 = price(pq, iq, d, 930, 'o'), price(pq, iq, d, 959, 'c')
            if None not in (a, b, e0, e1) and b != a:
                s = 1 if b > a else -1; r1 = s * (e1 - e0) / e0 - COST['NQ'] / e0
        rows['last half-hour momentum'].append(r1)
        # 2 NQ-ES spread reversion
        r2 = 0.0
        if not roll and d in eset:
            q0, q1, q2 = price(pq, iq, d, 570, 'o'), price(pq, iq, d, 659, 'c'), price(pq, iq, d, 954, 'c')
            s0, s1, s2 = price(pe, ie, d, 570, 'o'), price(pe, ie, d, 659, 'c'), price(pe, ie, d, 954, 'c')
            if None not in (q0, q1, q2, s0, s1, s2):
                dd = (q1 / q0 - 1) - (s1 / s0 - 1)
                if len(dsp_hist) >= 20:
                    sd = stt.pstdev(dsp_hist[-20:])
                    if sd and abs(dd) > 1.5 * sd:
                        side = -1 if dd > 0 else 1          # NQ led: short NQ, long ES
                        r2 = side * (q2 / q1 - 1) - side * (s2 / s1 - 1) - COST['NQ'] / q1 - COST['ES'] / s1
                dsp_hist.append(dd)
        rows['NQ-ES spread reversion'].append(r2)
        # 3 turn of the month: last trading day of the month + first three of the next (one round trip per block)
        nxt = dl[k + 1] if k + 1 < len(dl) else None
        last_day = nxt is not None and nxt[:7] != d[:7]
        pos = 1; j = k - 1
        while j >= 0 and dl[j][:7] == d[:7]: pos += 1; j -= 1
        tom = last_day or pos <= 3
        rows['turn of the month'].append((cc - (COST['NQ'] / D[p]['c'] if last_day else 0.0)) if tom else 0.0)
        # 4 pre-holiday: next weekday is not a trading day
        nd = dt.date.fromisoformat(d) + dt.timedelta(days=1)
        while nd.weekday() >= 5: nd += dt.timedelta(days=1)
        pre = nxt is not None and nd.isoformat() not in tradeset and nd.isoformat() < dl[-1]
        rows['pre-holiday'].append(cc - COST['NQ'] / D[p]['c'] if pre else 0.0)
    FROM = os.environ.get('B40_FROM')
    if FROM:                                   # descriptive look at one period only (e.g. 2026); changes no decision
        keep = [i for i, d in enumerate(days_used) if d >= FROM]
        days_used = [days_used[i] for i in keep]; core_cc = [core_cc[i] for i in keep]; core_on = [core_on[i] for i in keep]
        for kk in list(rows): rows[kk] = [rows[kk][i] for i in keep]
    rules = [rd.get(d, 0.0) for d in days_used]
    book = [a + b for a, b in zip(rules, core_cc)]
    out = dict(era=ERA, period=[days_used[0], days_used[-1]], book=dict(**stats(book)), ideas={})
    def corr(x, y):
        mx, my = stt.mean(x), stt.mean(y); sx, sy = stt.pstdev(x), stt.pstdev(y)
        return round(sum((a - mx) * (b - my) for a, b in zip(x, y)) / len(x) / (sx * sy), 3) if sx and sy else 0.0
    for name, x in rows.items():
        out['ideas'][name] = dict(own_sharpe=sr(x), active_days=sum(1 for v in x if v != 0), corr_with_book=corr(x, book),
                                  book_with_it=stats([a + b for a, b in zip(book, x)]))
    on_book = [a + b for a, b in zip(rules, core_on)]
    out['ideas']['overnight-only core'] = dict(own_sharpe=sr(core_on), current_core_sharpe=sr(core_cc), active_days=len(core_on),
                                               corr_with_book=corr(core_on, book), book_with_it=stats(on_book))
    json.dump(out, open(f"{A}/batch40_{ERA}{'_' + FROM[:4] if FROM else ''}.json", 'w'), indent=1); print(json.dumps(out, indent=1))

if __name__ == '__main__': main()
