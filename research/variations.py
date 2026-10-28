"""Variation comparison (28 Oct 2026), written and committed BEFORE running. Post-lockbox: all of 2011-2026 has been seen,
so this is in-sample by definition; the only clean test left is live paper trading from 1 Jan 2027.

Variations (structural only, no fine-tuning):
  V0 base: QuantLab + noise band + ATR band + expiry, equal 1R
  V1 drop QuantLab (it had no edge before costs on 2011-2020)
  V2 base + risk parity 12m (R01, the round-2 survivor)
  V3 drop QuantLab + risk parity 12m
  V4 base + cost rule: skip any trade whose round-trip cost is more than 10% of 1R (known at entry)
  V5 drop QuantLab + cost rule
  V6 drop QuantLab + cost rule + risk parity 12m
  V7 noise band + ATR band only (drop QuantLab and expiry)
Eras: A = 2011-2017 (calm), B = 2018-2020, C = Jul 2021 - Sep 2026.
SELECTION RULE (fixed now): pick the variation with the highest WORST-ERA Sharpe at normal costs, provided its all-era Sharpe at
double costs is at least the base's. Ties within 0.05: fewer moving parts wins (order V1 < V7 < V5 < V3 < V6 < V2 < V4 < V0).

  python research/variations.py run            (writes results/variations_<data>.json; run once per data folder)
  ARGON_DATA=lockbox2010 python research/variations.py run
  python research/variations.py combine        (reads both, applies the rule, writes results/VARIATIONS.md)"""
import os, sys, json, collections, statistics as stt
os.environ['ARGON_FULL'] = '1'
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
COSTCAP = 0.10
VARS = dict(V0=('ql nb atr exp', None, False), V1=('nb atr exp', None, False), V2=('ql nb atr exp', 12, False), V3=('nb atr exp', 12, False),
            V4=('ql nb atr exp', None, True), V5=('nb atr exp', None, True), V6=('nb atr exp', 12, True), V7=('nb atr', None, False))
SIMPLE = ['V1', 'V7', 'V5', 'V3', 'V6', 'V2', 'V4', 'V0']
ERAS = dict(A=('2011-01', '2017-12'), B=('2018-01', '2020-12'), C=('2021-07', '2026-09'))

def parity(ts, look):
    gm = collections.defaultdict(lambda: collections.defaultdict(float))
    for t in ts: gm[t['strat']][t['month']] += t['gross'] - t['cost']
    groups = sorted(gm); ms = sorted({t['month'] for t in ts}); import common as c
    am = c.months_between(ms[0], ms[-1]); W = {}
    for i, m in enumerate(am):
        prev = am[max(0, i - look):i]
        if len(prev) < look: continue
        sd = {g: stt.pstdev([gm[g].get(p, 0.0) for p in prev]) for g in groups}; inv = {g: 1 / v for g, v in sd.items() if v > 0}
        if inv: mu = sum(inv.values()) / len(inv); W[m] = {g: inv.get(g, mu) / mu for g in groups}
    return [dict(t, w=t['w'] * W.get(t['month'], {}).get(t['strat'], 1.0)) for t in ts]

def run():
    import common as c
    parts = dict(ql=c.walkforward(c.quantlab('NQ', skip_fomc=True)), nb=c.walkforward(c.noiseband('NQ')), atr=c.atrband('NQ'), exp=c.opex('NQ') + c.opex('ES'))
    parts2 = dict(ql=c.walkforward(c.quantlab('NQ', skip_fomc=True), 2.0), nb=c.walkforward(c.noiseband('NQ'), 2.0), atr=parts['atr'], exp=parts['exp'])
    out = {}
    for v, (who, look, cap) in VARS.items():
        for cx, P in ((1.0, parts), (2.0, parts2)):
            ts = [dict(t, w=1.0) for k in who.split() for t in P[k] if not (cap and t['cost'] > COSTCAP)]
            if look: ts = parity(ts, look)
            mm = collections.defaultdict(float)
            for t in ts: mm[t['month']] += t['w'] * (t['gross'] - cx * t['cost'])
            out[f'{v}|{cx}'] = dict(mm)
        print(v, 'done', flush=True)
    json.dump(out, open(f"{c.ROOT}/research/results/variations_{c.DATA}.json", 'w'))

def combine():
    import common as c
    M = {}
    for f in ('databento', 'lockbox2010'):
        for k, mm in json.load(open(f'{c.ROOT}/research/results/variations_{f}.json')).items(): M.setdefault(k, {}).update(mm)
    def ser(k, a, b): return [M[k].get(m, 0.0) for m in c.months_between(a, b)]
    rows = {}
    for v in VARS:
        e = {n: round(c.sharpe(ser(f'{v}|1.0', *r)), 2) for n, r in ERAS.items()}
        allm = ser(f'{v}|1.0', '2011-01', '2020-12') + ser(f'{v}|1.0', '2021-07', '2026-09')
        all2 = ser(f'{v}|2.0', '2011-01', '2020-12') + ser(f'{v}|2.0', '2021-07', '2026-09')
        rows[v] = dict(eras=e, worst=min(e.values()), all=round(c.sharpe(allm), 2), all_double=round(c.sharpe(all2), 2), R=round(sum(allm), 1),
                       R_eras={n: round(sum(ser(f'{v}|1.0', *r)), 1) for n, r in ERAS.items()})
    ok = [v for v in VARS if rows[v]['all_double'] >= rows['V0']['all_double']]
    best = max(r['worst'] for v, r in rows.items() if v in ok)
    pick = next(v for v in SIMPLE if v in ok and rows[v]['worst'] >= best - 0.05)
    L = ['# Variation comparison (in-sample, post-lockbox)', '', 'Rule fixed before running: highest worst-era Sharpe, double-cost Sharpe at least the base, ties to the simpler one.', '',
         '| | 2011-17 | 2018-20 | 2021-26 | worst era | all eras | all, 2x costs | total R |', '|---|---|---|---|---|---|---|---|']
    names = dict(V0='base (4 strategies)', V1='drop QuantLab', V2='base + risk parity', V3='drop QuantLab + risk parity', V4='base + cost rule',
                 V5='drop QuantLab + cost rule', V6='drop QuantLab + cost rule + risk parity', V7='noise band + ATR band only')
    for v, r in rows.items():
        L.append(f"| {v} {names[v]}{' **(pick)**' if v == pick else ''} | {r['eras']['A']} | {r['eras']['B']} | {r['eras']['C']} | {r['worst']} | {r['all']} | {r['all_double']} | {r['R']} |")
    open(f'{c.ROOT}/research/results/VARIATIONS.md', 'w').write('\n'.join(L) + '\n'); json.dump(dict(rows=rows, pick=pick), open(f'{c.ROOT}/research/results/variations.json', 'w'), indent=1)
    print('\n'.join(L))

if __name__ == '__main__':
    run() if sys.argv[1:] == ['run'] else combine()
