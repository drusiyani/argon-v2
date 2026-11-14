"""Batch 22 (14 Nov 2026). What is tested and how it is read: analysis/BATCH22_PREREG.md (committed before this file ran).
Run once per era."""

import os, sys, json, math, csv, random, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'engine'))
import portfolio as P
c = P.c
ERA = os.environ.get('ARGON_DATA', 'databento'); risk = P.CONFIG['risk_pct'] / 100; cap = P.CONFIG['cost_cap_R']
LO, HI = (('2021-01-01', '2026-12-31') if ERA == 'databento' else ('2010-07-01', '2020-12-31'))
PC = {'2011-04-27', '2011-06-22', '2011-11-02', '2012-01-25', '2012-04-25', '2012-06-20', '2012-09-13', '2012-12-12'}
def csvmap(fn, col): return {r['date']: float(r[col]) for r in csv.DictReader(open(os.path.join(ROOT, 'analysis', fn)))}
TB = {d: v / 100 / 252 for d, v in csvmap('tbill_dtb3.csv', 'dtb3_pct').items()} if False else None
TB = {r['date']: float(r['dtb3_pct']) / 100 / 252 for r in csv.DictReader(open(os.path.join(ROOT, 'analysis', 'tbill_dtb3.csv')))}

def skipset(S):
    out = {'roll': set(), 'bad': set()}
    for f, k in (('roll', 'roll'), ('bad_days', 'bad')):
        try:
            v = getattr(c, f)(S); v = v.keys() if isinstance(v, dict) else v; out[k] = {x for x in v if isinstance(x, str) and len(x) == 10}
        except Exception: pass
    return out

def lastbefore(src, keys, d):
    import bisect
    i = bisect.bisect_left(keys, d); return (src[keys[i - 1]], i - 1) if i > 0 else (None, -1)

def build(S, volfile, volcol, book_trades):
    D, dl, _ = c.daily(S); T, O, H, L, C, n, mins, days, wd = c.prep(S); sk = skipset(S)
    ret_fix, ret_old = {}, {}
    for k in range(1, len(dl)):
        d, p = dl[k], dl[k - 1]; r = D[d]['c'] / D[p]['c'] - 1
        bad = d in sk['bad'] or p in sk['bad']; roll = d in sk['roll'] or p in sk['roll']
        ret_old[d] = 0.0 if (bad or roll or abs(r) > 0.15) else r
        ret_fix[d] = 0.0 if bad else ((D[d]['c'] / D[d]['o'] - 1) if (roll or abs(r) > 0.15) else r)
    V = csvmap(volfile, volcol); vk = sorted(V); tbk = sorted(TB)
    def volw(d, prev_day):
        v, i = lastbefore(V, vk, prev_day)
        if not v: return 1.0
        h = sorted(V[x] for x in vk[max(0, i - 251):i + 1]); med = h[len(h) // 2] if len(h) >= 60 else v
        return min(1.5, med / v)
    pos = {d: k for k, d in enumerate(dl)}
    w_fix = {dl[k]: volw(dl[k], dl[k - 1]) for k in range(1, len(dl))}            # vol index known before yesterday's close
    w_old = {dl[k]: volw(dl[k], dl[k]) for k in range(1, len(dl))}                # the 11 Nov version (yesterday's close print)
    tb = {d: (lastbefore(TB, tbk, d)[0] or 0.0) for d in dl}
    def fomc(fixed):
        out = {}
        for d in sorted(c.FOMC):
            if d not in pos or pos[d] == 0: continue
            p = dl[pos[d] - 1]
            if d in sk['bad'] or p in sk['bad'] or ((d in sk['roll'] or p in sk['roll']) and not fixed): continue
            lim = 734 if (fixed and d in PC) else 839
            i2 = [i for i in D[d]['r'] if mins[i] <= lim]
            if i2: out[d] = C[i2[-1]] / D[p]['c'] - 1 - c.COST[S] / D[p]['c']
        return out
    f_fix, f_old = fomc(True), fomc(False)
    bk = collections.defaultdict(float); bl = collections.defaultdict(float)
    for t in book_trades:
        x = t.get('w', 1.0) * (t['gross'] - t['cost']); bk[t['date']] += x
        if t['strat'] == 'expiry' or t['side'] in (1, 'long'): bl[t['date']] += x
    return dict(dl=dl, ret_fix=ret_fix, ret_old=ret_old, w_fix=w_fix, w_old=w_old, tb=tb, f_fix=f_fix, f_old=f_old, bk=bk, bl=bl)

def metrics(x):
    eq, peak, dd = 1.0, 1.0, 0.0
    for v in x: eq *= 1 + v; peak = max(peak, eq); dd = min(dd, eq / peak - 1)
    n_ = len(x); m = sum(x) / n_; s = math.sqrt(sum((v - m) ** 2 for v in x) / (n_ - 1)) or 1e-12
    dn = math.sqrt(sum(min(0.0, v) ** 2 for v in x) / n_) or 1e-12
    return dict(final_usd=round(100000 * eq), cagr_pct=round(100 * (max(eq, 1e-9) ** (252 / n_) - 1), 1), sharpe=round(m / s * math.sqrt(252), 2),
                sortino=round(m / dn * math.sqrt(252), 2), worst_drop_pct=round(100 * dd, 1))

def boot(SER, draws=1000, B=63, seed=20261111):
    rng = random.Random(seed); N = len(next(iter(SER.values()))); res = {k: [] for k in SER}
    for _ in range(draws):
        idx = []
        while len(idx) < N: st = rng.randrange(0, N - B); idx.extend(range(st, st + B))
        idx = idx[:N]
        for k, v in SER.items():
            eq, peak, dd = 1.0, 1.0, 0.0
            for i in idx: eq *= 1 + v[i]; peak = max(peak, eq); dd = min(dd, eq / peak - 1)
            res[k].append((max(eq, 1e-9) ** (252 / N) - 1, dd))
    out = {}
    for k, v in res.items():
        cg = sorted(a for a, _ in v); dd = [b for _, b in v]
        out[k] = dict(median_cagr_pct=round(100 * cg[len(cg) // 2], 1), bad_case_cagr_pct_5th=round(100 * cg[len(cg) // 20], 1),
                      chance_losing_money_pct=round(100 * sum(a < 0 for a, _ in v) / draws, 1),
                      chance_drop_worse_than_35_pct=round(100 * sum(b < -.35 for b in dd) / draws, 1))
    return out




kw = P.CONFIG['strategies']; REF = {'NQ': 28387.75, 'ES': 7616.25}; RULES = ('quantlab', 'noiseband', 'atrband')
def run_rules(sym): return dict(quantlab=c.quantlab(sym, **kw['quantlab']), noiseband=c.noiseband(sym, **kw['noiseband']), atrband=c.atrband(sym, **kw['atrband']))
raw = P.raw(); trades0 = P.book(1.0)
REAL = {'NQ': {k: raw[k] for k in RULES}, 'ES': run_rules('ES')}
SL0, C0 = dict(c.SL), dict(c.COST); c.SL = {k: 0.0 for k in SL0}; c.COST = {k: 0.0 for k in C0}
FREE = {s: run_rules(s) for s in ('NQ', 'ES')}
c.SL, c.COST = SL0, C0
key = lambda t: (t['date'], t['variant'], t['entry_min'])
FMAP = {s: {r: {key(t): t['gross'] * t['risk_pts'] for t in FREE[s][r]} for r in RULES} for s in FREE}
# ---- Part 1: friction-free result of the picked trades, before the cost rule
part1 = {}
for s in ('NQ', 'ES'):
    picked = c.walkforward(REAL[s]['quantlab'], 1.0) + c.walkforward(REAL[s]['noiseband'], 1.0) + list(REAL[s]['atrband']); tab = {}
    for t in picked:
        if not (LO <= t['date'] <= HI): continue
        q = tab.setdefault(t['date'][:4], {}).setdefault(t['strat'], dict(n=0, matched=0, real_net=0.0, real_before_commission=0.0, friction_free=0.0, kept_by_cost_rule=0))
        q['n'] += 1; q['real_net'] += t['gross'] - t['cost']; q['real_before_commission'] += t['gross']; q['kept_by_cost_rule'] += t['cost'] <= cap
        f = FMAP[s][t['strat']].get(key(t))
        if f is not None: q['matched'] += 1; q['friction_free'] += f / t['risk_pts']
    for y in tab:
        tot = dict(n=0, matched=0, real_net=0.0, real_before_commission=0.0, friction_free=0.0, kept_by_cost_rule=0)
        for r in tab[y].values():
            for k_ in tot: tot[k_] += r[k_]
        tab[y]['all three'] = tot
        for r in tab[y].values():
            for k_ in ('real_net', 'real_before_commission', 'friction_free'): r[k_] = round(r[k_], 1)
    part1[s] = dict(sorted(tab.items()))
# ---- Part 2: scenario at today's relative friction (Nasdaq)
miss = collections.Counter()
def scen(trs):
    out = []
    for t in trs:
        sc = t['entry'] / REF[t['sym']]; real = t['gross'] * t['risk_pts']; f = FMAP[t['sym']][t['strat']].get(key(t))
        if f is None: miss[t['strat']] += 1; f = real                       # unmatched: keeps its real slippage (conservative)
        u = dict(t); u['gross'] = (f * (1 - sc) + real * sc) / t['risk_pts']; u['cost'] = C0[t['sym']] * sc / t['risk_pts']; out.append(u)
    return out
book_s = [dict(t) for t in c.walkforward(scen(raw['quantlab']), 1.0)] + [dict(t) for t in c.walkforward(scen(raw['noiseband']), 1.0)] + [dict(t) for t in scen(raw['atrband'])] + [dict(t) for t in raw['expiry']]
book_s = [t for t in book_s if t['cost'] <= cap]
for t in book_s: t['w'] = 1.0
base = build('NQ', 'vxn.csv', 'vxn', trades0); dl = base['dl']
first = min(t['date'] for t in trades0); days = [d for d in dl[1:] if max(LO, first) <= d <= HI]
core = {d: base['w_fix'][d] * base['ret_fix'][d] + base['f_fix'].get(d, 0.0) for d in dl[1:]}
def series(tr, rw=0.5):
    R = collections.defaultdict(float)
    for t in tr: R[t['date']] += t.get('w', 1.0) * (t['gross'] - t['cost'])
    return [core[d] + rw * risk * R.get(d, 0.0) + base['tb'][d] for d in days]
SER = {'package, real friction': series(trades0), "package, today's friction (scenario)": series(book_s), 'core only': series([])}
hist_ = {k: metrics(v) for k, v in SER.items()}; bt = boot(SER)
PER = (('2010-17', '2010', '2018'), ('2018-20', '2018', '2021'), ('2021-25', '2021', '2026'), ('2026', '2026', '2027')); subs = {}
for nm, x in SER.items():
    for lab, a, b in PER:
        seg = [v for v, d in zip(x, days) if a <= d < b]
        if len(seg) > 60: m = metrics(seg); subs.setdefault(nm, {})[lab] = dict(cagr_pct=m['cagr_pct'], worst_drop_pct=m['worst_drop_pct'])
def byyear(tr):
    o = {}
    for t in tr:
        if t['date'] in set(days) and t['strat'] != 'expiry':
            q = o.setdefault(t['date'][:4], dict(n=0, R=0.0, ql=0)); q['n'] += 1; q['R'] += t['gross'] - t['cost']; q['ql'] += t['strat'] == 'quantlab'
    return {y: dict(trades=v['n'], quantlab_trades=v['ql'], net_R=round(v['R'], 1)) for y, v in sorted(o.items())}
out = dict(era=ERA, part1=part1, scenario=dict(history=hist_, bootstrap={k: v['chance_drop_worse_than_35_pct'] for k, v in bt.items()}, sub_periods=subs,
           rules_by_year=dict(real=byyear(trades0), scenario=byyear(book_s)), unmatched=dict(miss), raw_counts={r: len(raw[r]) for r in RULES}))
json.dump(out, open(os.path.join(ROOT, 'analysis', f'batch22_{ERA}.json'), 'w'), indent=1)
for s in part1:
    for y, v in part1[s].items(): a = v['all three']; print(s, y, 'n', a['n'], 'matched', a['matched'], 'real net', a['real_net'], 'before commission', a['real_before_commission'], 'friction-free', a['friction_free'], '| QL', v.get('quantlab', {}).get('friction_free'), 'NB', v.get('noiseband', {}).get('friction_free'), 'AB', v.get('atrband', {}).get('friction_free'))
for k, v in hist_.items(): print(k, v, bt[k]['chance_drop_worse_than_35_pct'])
print(json.dumps(subs)); print(json.dumps(out['scenario']['rules_by_year'])); print('unmatched', dict(miss), out['scenario']['raw_counts'])
