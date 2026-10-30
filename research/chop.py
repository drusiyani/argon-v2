"""The chop strategy, "Fade the stretch". Rules and pass marks committed BEFORE the test runs (30 Oct 2026).
Every year of NQ data has already been seen, so this is an in-sample test by design; the pass marks are strict to compensate.

RULES (NQ, regular session, fixed in advance, from the research on mean reversion in calm markets):
  - Calm days only: yesterday's 9:30-16:00 range < CALM x the average of the 20 sessions before it (CALM = 0.8, the same cut-off
    as the pre-registered one-line sizing rule).
  - Every 15-minute close from 10:00 to 15:00: if price is more than BAND x daily ATR(14) above the open, sell; below, buy
    (BAND = 0.35). Entry at the next minute's open + 1 tick.
  - Target: the session open, as a limit order (fills only if price trades 1 tick through). Stop: open +/- 0.7 x ATR, 1 tick slippage.
  - Flat at 15:55 (FOMC days at the usual early exit). One trade a day. Roll days and half days skipped.
  - Same costs (0.75 NQ points a round trip) and the same cost rule as the book (skip if costs > 10% of 1R).
PASS MARKS (all four):
  1. Positive net R in 2011-2017 AND in 2018-2026 (2018-2020 + Jul 2021-Sep 2026), separately.
  2. Adding it to the v2 book raises the book's monthly Sharpe by >= +0.05 in both of those eras, and its monthly correlation with
     the book is below 0.3.
  3. Still positive overall at double costs.
  4. All four nearby settings positive overall: BAND 0.25 and 0.45; CALM 0.7 and 0.9.
If it passes: Dru decides whether it becomes strategy five, logged as an amendment before the 31 Dec freeze. If it fails: it is out.

  python research/chop.py run                          (2021-2026 data)
  ARGON_DATA=lockbox2010 python research/chop.py run   (2011-2020 data)
  python research/chop.py judge                        (applies the pass marks, writes results/CHOP.md)"""
import os, sys, json, collections, statistics as stt
os.environ['ARGON_FULL'] = '1'; HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
SETTINGS = dict(base=(0.35, 0.8), band_lo=(0.25, 0.8), band_hi=(0.45, 0.8), calm_lo=(0.35, 0.7), calm_hi=(0.35, 0.9))

def chop(c, band=0.35, calm=0.8, stop_k=0.7, s='NQ'):
    P = c.prep(s); T, O, H, L, C, n, mins, days, wd = P; D, dl, atr = c.daily(s); R = c.roll(s); TK = c.SL[s]; out = []
    rng = {d: D[d]['h'] - D[d]['l'] for d in dl}
    for k, d in enumerate(dl):
        if k < 22 or d not in atr or d in R or d in c.bad_days(s): continue
        prev = dl[k - 1]; avg = stt.mean(rng[x] for x in dl[k - 21:k - 1])
        if not rng[prev] < calm * avg: continue
        r = D[d]['r']; op = D[d]['o']; a = atr[d]; ex = c.fexit(d) if d in c.FOMC else 955
        for q, i in enumerate(r):
            m = mins[i]
            if m > 900 or m >= ex: break
            if m < 599 or m % 15 != 14 or q + 1 >= len(r): continue
            side = -1 if C[i] > op + band * a else (1 if C[i] < op - band * a else 0)
            if not side: continue
            e = r[q + 1]; entry = O[e] + side * TK; stop = op - side * stop_k * a; tgt = op; risk = (entry - stop) * side
            if risk <= 2 * TK: break
            res = None; xm = None
            for x in r[q + 1:]:
                if mins[x] >= ex: res = (C[x] - entry) * side; xm = mins[x]; break
                if (L[x] <= stop) if side == 1 else (H[x] >= stop): res = (stop - side * TK - entry) * side; xm = mins[x]; break
                if (H[x] >= tgt + TK) if side == 1 else (L[x] <= tgt - TK): res = (tgt - entry) * side; xm = mins[x]; break
            if res is None: res = (C[r[-1]] - entry) * side; xm = mins[r[-1]]
            out.append(c.trade('chop', s, d, 0, side, mins[e], xm, risk, res)); break
    return [t for t in out if t['cost'] <= 0.10]

def run():
    import common as c
    res = {}
    for name, (band, calm) in SETTINGS.items():
        t = chop(c, band, calm); mm1 = collections.defaultdict(float); mm2 = collections.defaultdict(float)
        for x in t: mm1[x['month']] += x['gross'] - x['cost']; mm2[x['month']] += x['gross'] - 2 * x['cost']
        res[name] = dict(n=len(t), m1=dict(mm1), m2=dict(mm2), gross=round(sum(x['gross'] for x in t), 2), win=round(100 * sum(1 for x in t if x['gross'] - x['cost'] > 0) / max(1, len(t)), 1))
        print(c.DATA, name, len(t), 'trades', round(sum(mm1.values()), 1), 'R', flush=True)
    json.dump(res, open(f'{c.ROOT}/research/results/chop_{c.DATA}.json', 'w'))

def judge():
    import common as c
    M = {}; cnt = collections.Counter(); win = {}; gross = collections.Counter()
    for f in ('databento', 'lockbox2010'):
        for k, v in json.load(open(f'{c.ROOT}/research/results/chop_{f}.json')).items():
            M.setdefault(k, {'m1': {}, 'm2': {}}); M[k]['m1'].update(v['m1']); M[k]['m2'].update(v['m2']); cnt[k] += v['n']; gross[k] += v['gross']; win[k] = v['win']
    book = {}
    for f in ('databento', 'lockbox2010'): book.update(json.load(open(f'{c.ROOT}/research/results/variations_{f}.json'))['V4|1.0'])
    A = c.months_between('2011-01', '2017-12'); B = c.months_between('2018-01', '2020-12') + c.months_between('2021-07', '2026-09')
    ser = lambda d, ms: [d.get(m, 0.0) for m in ms]
    def corr(x, y):
        mx, my = stt.mean(x), stt.mean(y); sx, sy = stt.pstdev(x), stt.pstdev(y)
        return sum((a - mx) * (b - my) for a, b in zip(x, y)) / len(x) / (sx * sy) if sx and sy else 0
    base = M['base']; out = {}
    for era, ms in (('2011-17', A), ('2018-26', B)):
        ch = ser(base['m1'], ms); bk = ser(book, ms); comb = [a + b for a, b in zip(ch, bk)]
        out[era] = dict(chop_R=round(sum(ch), 1), book_sharpe=round(c.sharpe(bk), 3), with_chop=round(c.sharpe(comb), 3), corr=round(corr(ch, bk), 2))
    allm = A + B
    checks = {'1 positive in both eras': all(out[e]['chop_R'] > 0 for e in out),
              '2 lifts the book by +0.05 in both eras, correlation < 0.3': all(out[e]['with_chop'] - out[e]['book_sharpe'] >= 0.05 and out[e]['corr'] < 0.3 for e in out),
              '3 positive at double costs': sum(ser(base['m2'], allm)) > 0,
              '4 every nearby setting positive': all(sum(ser(M[k]['m1'], allm)) > 0 for k in SETTINGS if k != 'base')}
    verdict = 'PASS' if all(checks.values()) else 'FAIL'
    L = ['# The chop strategy, "Fade the stretch": result', '', f'Rules and pass marks were committed before this ran. Verdict: **{verdict}**', '',
         '| | 2011–2017 | 2018–2026 |', '|---|---|---|',
         f"| Chop result | {out['2011-17']['chop_R']:+}R | {out['2018-26']['chop_R']:+}R |",
         f"| Book Sharpe without it | {out['2011-17']['book_sharpe']} | {out['2018-26']['book_sharpe']} |",
         f"| Book Sharpe with it | {out['2011-17']['with_chop']} | {out['2018-26']['with_chop']} |",
         f"| Correlation with the book | {out['2011-17']['corr']} | {out['2018-26']['corr']} |", '',
         f"Trades: {cnt['base']}, win rate {win.get('base')}%, before costs {gross['base']:+.1f}R, at double costs {sum(ser(base['m2'], allm)):+.1f}R.", '',
         '| Nearby setting | Total R |', '|---|---|'] + [f"| {k} | {sum(ser(M[k]['m1'], allm)):+.1f}R |" for k in SETTINGS] + ['', '## Checks', ''] + [f"- {k}: {'yes' if v else 'no'}" for k, v in checks.items()]
    open(f'{c.ROOT}/research/results/CHOP.md', 'w').write('\n'.join(L) + '\n'); json.dump(dict(eras=out, checks=checks, verdict=verdict), open(f'{c.ROOT}/research/results/chop.json', 'w'), indent=1)
    print('\n'.join(L))

if __name__ == '__main__':
    run() if sys.argv[1:] == ['run'] else judge()
