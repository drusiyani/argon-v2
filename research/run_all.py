"""Test every pre-registered adjustment (research/adjustments.py) on Jul 2021 - Dec 2024 ONLY.

  python research/run_all.py            -> test window. Saves research/results/adj/<id>.json after EACH test and skips
                                           ones already saved, so a timed-out run just carries on next time.
  ARGON_LOCKBOX=open python research/run_all.py lockbox
                                        -> runs the survivors ONCE on 2025-01..2026-09. Refuses to run twice.
Portfolio rules use each trade's exact entry and exit minute (a trade only "knows" about trades that closed before it
opened), so the old daily-total lookahead is gone."""
import os, sys, json, time, copy, random, collections, datetime as dt, statistics as stt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as c, adjustments as adj

MODE = sys.argv[1] if len(sys.argv) > 1 else 'test'
OUT = os.environ.get('ARGON_OUT', c.ROOT + '/research/results'); ADJ_DIR = OUT + '/adj'; os.makedirs(ADJ_DIR, exist_ok=True)
if MODE == 'lockbox':
    if not c.OPEN: sys.exit('lockbox needs ARGON_LOCKBOX=open')
    if os.path.exists(OUT + '/lockbox.json'): sys.exit('the lockbox has already been opened once. No retries.')
    MONTHS = c.months_between(c.LOCK_START, c.FULL_END)
else:
    if c.OPEN: sys.exit('test mode must run with the lockbox closed')
    MONTHS = c.months_between(c.FIRST_MONTH, c.TEST_END)
MSET = set(MONTHS); YEARS = sorted({m[:4] for m in MONTHS})
GROUPS = ('quantlab', 'noiseband', 'atrband', 'expiry')
T0 = time.time()
def log(*a): print(f'[{(time.time() - T0) / 60:6.1f}m]', *a, flush=True)

# ---------------------------------------------------------------- strategy trades (raw cached, walk-forward per cost level)
_RAW = {}
def raw(name, kw):
    key = (name, json.dumps(kw, sort_keys=True, default=str))
    if key not in _RAW:
        if name == 'quantlab': _RAW[key] = c.quantlab('NQ', **kw)
        elif name == 'noiseband': _RAW[key] = c.noiseband('NQ', **kw)
        elif name == 'atrband': _RAW[key] = c.atrband('NQ', **kw)
        else: _RAW[key] = c.opex('NQ', **kw) + c.opex('ES', **kw)
    return _RAW[key]

def strat(name, kw, cx):
    kw = dict(kw); look = kw.pop('_look', 6); pick = kw.pop('_pick', 'sum')
    if 'chands' in kw: kw['chands'] = tuple(kw['chands'])
    for k in ('stops', 'freqs', 'mults'):
        if k in kw: kw[k] = tuple(kw[k])
    r = raw(name, kw)
    t = c.walkforward(r, cx, look, pick) if name in ('quantlab', 'noiseband') else list(r)
    return [dict(x, w=1.0) for x in t]

def book(cx, over=None):
    over = over or {}; out = []
    for g in GROUPS: out += strat(g, over.get(g, {}), cx)
    out.sort(key=lambda t: (t['date'], t['entry_min'], t['exit_min']))
    return out

def R(t, cx): return t['w'] * (t['gross'] - cx * t['cost'])

# ---------------------------------------------------------------- portfolio rules (exact times)
def by_day(ts):
    d = collections.defaultdict(list)
    for t in ts: d[t['date']].append(t)
    return d

def sequential(ts, cx, decide, reset='day'):
    """Walk trades in entry order. decide(t, realised, open_trades, state) -> new weight. Only trades that EXITED before
    t's entry minute count as realised; trades with entry <= t.entry < exit are open."""
    key = (lambda t: t['date']) if reset == 'day' else (lambda t: dt.date.fromisoformat(t['date']).isocalendar()[:2])
    groups = collections.defaultdict(list)
    for t in ts: groups[key(t)].append(t)
    for k in sorted(groups):
        acc = []; state = {}
        for t in sorted(groups[k], key=lambda t: (t['date'], t['entry_min'])):
            now = (t['date'], t['entry_min'])
            realised = sum(R(a, cx) for a in acc if (a['date'], a['exit_min']) < now)
            openl = [a for a in acc if (a['date'], a['exit_min']) >= now and a['date'] == t['date']]
            t['w'] = decide(t, realised, openl, state)
            if t['w'] > 0: acc.append(t)
    return ts

def third_friday(d):
    x = dt.date.fromisoformat(d); return x.weekday() == 4 and 15 <= x.day <= 21

def group_monthly(ts, cx):
    g = collections.defaultdict(lambda: collections.defaultdict(float))
    for t in ts: g[t['strat']][t['month']] += t['gross'] - cx * t['cost']
    return g

def month_weights(ts, cx, fn, look):
    gm = group_monthly(ts, cx); allm = c.months_between('2021-01', max(t['month'] for t in ts))
    W = {}
    for i, m in enumerate(allm):
        prev = allm[max(0, i - look):i]
        W[m] = fn({g: [gm[g].get(p, 0.0) for p in prev] for g in GROUPS}, len(prev) >= look)
    for t in ts: t['w'] *= W.get(t['month'], {}).get(t['strat'], 1.0)
    return ts

def apply(rule, kw, ts, cx):
    if rule is None: return ts
    if rule == 'chain':
        for r, k in kw['steps']: ts = apply(r, k, ts, cx)
        return ts
    if rule == 'netcost':
        q = collections.defaultdict(list)
        for t in ts:
            if t['w'] <= 0: continue
            n = t['w'] / t['risk_pts']
            q[(t['date'], t['sym'], t['entry_min'])].append(t['side'] * n); q[(t['date'], t['sym'], t['exit_min'])].append(-t['side'] * n)
        save = collections.defaultdict(float)
        for (d, s, m), xs in q.items():
            if len(xs) > 1: save[d] += (sum(abs(x) for x in xs) - abs(sum(xs))) * c.COST[s] / 2
        return ts + [dict(strat='netting', sym='NQ', date=d, month=d[:7], entry_min=0, exit_min=0, side=0, risk_pts=1, gross=0.0, cost=-v, w=1.0) for d, v in save.items()]
    if rule == 'opposite':
        def f(t, rl, op, st):
            if t['sym'] == 'NQ' and any(a['sym'] == 'NQ' and a['side'] == -t['side'] for a in op): return 0.0 if kw['mode'] == 'skip' else t['w'] * 0.5
            return t['w']
        return sequential(ts, cx, f)
    if rule == 'losslimit':
        L = kw['L']; orisk = kw.get('openrisk', False)
        def f(t, rl, op, st):
            worst = rl - (sum(a['w'] for a in op) + t['w'] if orisk else 0)
            return 0.0 if (rl <= -L or (orisk and worst < -L)) else t['w']
        return sequential(ts, cx, f)
    if rule == 'profitlock':
        return sequential(ts, cx, lambda t, rl, op, st: 0.0 if rl >= kw['P'] else t['w'])
    if rule == 'riskcap':
        cap = kw['cap']
        def f(t, rl, op, st):
            o = sum(a['w'] for a in op)
            if o + t['w'] <= cap + 1e-9: return t['w']
            if kw.get('scale') and cap - o >= 0.25: return cap - o
            return 0.0
        return sequential(ts, cx, f)
    if rule == 'weeklimit':
        return sequential(ts, cx, lambda t, rl, op, st: 0.0 if rl <= -kw['L'] else t['w'], reset='week')
    if rule == 'stack':
        return sequential(ts, cx, lambda t, rl, op, st: 0.0 if t['sym'] == 'NQ' and sum(1 for a in op if a['sym'] == 'NQ' and a['side'] == t['side']) >= kw['k'] else t['w'])
    if rule == 'maxopen':
        return sequential(ts, cx, lambda t, rl, op, st: 0.0 if t['sym'] == 'NQ' and sum(1 for a in op if a['sym'] == 'NQ') >= kw['k'] else t['w'])
    if rule == 'pairstack':
        P2 = ('noiseband', 'atrband')
        return sequential(ts, cx, lambda t, rl, op, st: 0.0 if t['strat'] in P2 and sum(1 for a in op if a['strat'] in P2 and a['side'] == t['side']) >= kw['k'] else t['w'])
    if rule == 'maxday':
        def f(t, rl, op, st):
            st['n'] = st.get('n', 0) + 1; return t['w'] if st['n'] <= kw['k'] else 0.0
        return sequential(ts, cx, f)
    if rule == 'cooldown':
        def f(t, rl, op, st): return t['w']
        for d, xs in by_day(ts).items():
            acc = []
            for t in sorted(xs, key=lambda t: t['entry_min']):
                if any(R(a, cx) < 0 and a['exit_min'] < t['entry_min'] <= a['exit_min'] + kw['m'] for a in acc): t['w'] = 0.0
                if t['w'] > 0: acc.append(t)
        return ts
    if rule in ('agree', 'against'):
        for d, xs in by_day(ts).items():
            ql = [t for t in xs if t['strat'] == 'quantlab' and t['w'] > 0]
            if not ql: continue
            q = ql[0]
            for t in xs:
                if t['strat'] in ('noiseband', 'atrband') and t['entry_min'] > q['entry_min']:
                    if rule == 'agree' and t['side'] == q['side']: t['w'] *= kw['boost']
                    if rule == 'against' and t['side'] != q['side']: t['w'] = 0.0 if kw['mode'] == 'skip' else t['w'] * 0.5
        return ts
    if rule == 'weights':
        for t in ts:
            for k, v in kw['w'].items():
                if t['strat'] == k or f"{t['strat']}_{t['sym']}" == k: t['w'] *= v
        return ts
    if rule == 'skipdays':
        for t in ts:
            x = dt.date.fromisoformat(t['date'])
            if (kw['rule'] == 'first_friday' and x.weekday() == 4 and x.day <= 7) or (kw['rule'] == 'fomc' and t['date'] in c.FOMC): t['w'] = 0.0
        return ts
    if rule == 'qlexpiry':
        for t in ts:
            if t['strat'] == 'quantlab' and third_friday(t['date']):
                if kw['mode'] == 'skip_long' and t['side'] == 1: t['w'] = 0.0
                if kw['mode'] == 'half': t['w'] *= 0.5
        return ts
    if rule == 'parity':
        lo, hi = kw.get('lo'), kw.get('hi')
        def fn(hist, ok):
            if not ok: return {}
            inv = {g: (1 / stt.pstdev(x) if stt.pstdev(x) > 0 else None) for g, x in hist.items()}
            v = [x for x in inv.values() if x]
            if not v: return {}
            mu = sum(v) / len(v); w = {g: (x / mu if x else 1.0) for g, x in inv.items()}
            if lo is not None: w = {g: min(hi, max(lo, x)) for g, x in w.items()}
            return w
        return month_weights(ts, cx, fn, kw['look'])
    if rule == 'sharpew':
        def fn(hist, ok):
            if not ok: return {}
            s = {g: max(0.0, c.sharpe(x)) for g, x in hist.items()}; tot = sum(s.values())
            return {g: v * len(s) / tot for g, v in s.items()} if tot > 0 else {}
        return month_weights(ts, cx, fn, kw['look'])
    if rule == 'kill':
        return month_weights(ts, cx, lambda hist, ok: {g: (0.0 if ok and sum(x) < 0 else 1.0) for g, x in hist.items()}, kw['look'])
    if rule == 'ddctl':
        mm = collections.defaultdict(list)
        for t in ts: mm[t['month']].append(t)
        eq = pk = 0.0
        for m in sorted(mm):
            half = pk - eq > kw['dd']
            for t in mm[m]:
                if half: t['w'] *= 0.5
            eq += sum(R(t, cx) for t in mm[m]); pk = max(pk, eq)
        return ts
    if rule == 'streak':
        days = by_day(ts); run = 0
        for d in sorted(days):
            if run >= kw['n']:
                for t in days[d]: t['w'] *= 0.5
            r = sum(R(t, cx) for t in days[d] if t['w'] > 0)
            run = run + 1 if r < 0 else 0
        return ts
    raise ValueError(rule)

# ---------------------------------------------------------------- scoring
def series(ts, cx):
    mm = collections.defaultdict(float)
    for t in ts:
        if t['month'] in MSET: mm[t['month']] += R(t, cx)
    return [mm.get(m, 0.0) for m in MONTHS]

def score(ts, cx):
    s = series(ts, cx)
    yrs = {y: round(sum(v for m, v in zip(MONTHS, s) if m[:4] == y), 2) for y in YEARS}
    return dict(sharpe=round(c.sharpe(s), 3), R=round(sum(s), 2), years=yrs, trades=sum(1 for t in ts if t['month'] in MSET and t['w'] > 0 and t['side'] != 0))

def run_one(a, kw, cx):
    if a['kind'] == 'strat': ts = book(cx, {a['target']: kw})
    elif a['kind'] == 'multi': ts = book(cx, kw)
    else: ts = apply(a['target'], copy.deepcopy(kw), book(cx), cx)
    return score(ts, cx)

def grow(s, risk):
    eq = pk = 1.0; dd = 0.0
    for v in s: eq *= max(0.0, 1 + v * risk / 100); pk = max(pk, eq); dd = min(dd, eq / pk - 1)
    return eq, dd

def sizing(risk):
    s = series(book(1.0), 1.0); eq, dd = grow(s, risk); rg = random.Random(7); n = len(s); halved = 0
    for _ in range(3000):
        y = []
        while len(y) < n: k = rg.randrange(0, n - 2); y += s[k:k + 3]
        if grow(y[:n], risk)[1] <= -0.5: halved += 1
    return dict(risk=risk, a_year=round((eq ** (12 / n) - 1) * 100, 1), worst_drop=round(dd * 100, 1), halving_chance=round(100 * halved / 3000, 1))

# ---------------------------------------------------------------- main
def test_mode():
    P = adj.PASS; base = {cx: score(book(cx), cx) for cx in (1.0, 2.0)}
    json.dump(dict(window=[MONTHS[0], MONTHS[-1]], normal=base[1.0], double=base[2.0]), open(OUT + '/baseline.json', 'w'), indent=1)
    log('baseline', base[1.0]['sharpe'], 'double', base[2.0]['sharpe'])
    only = set(filter(None, os.environ.get('ONLY', '').split(',')))
    for a in adj.A:
        if only and a['id'] not in only: continue
        f = f"{ADJ_DIR}/{a['id']}.json"
        if os.path.exists(f): continue
        log(a['id'], a['name'])
        try:
            if a['kind'] == 'size':
                res = dict(id=a['id'], name=a['name'], kind='size', report=sizing(a['kw']['risk']), verdict='reported')
            else:
                n = run_one(a, a['kw'], 1.0); d2 = run_one(a, a['kw'], 2.0)
                near = [dict(kw=k, **run_one(a, k, 1.0)) for k in (a['nearby'] or [])]
                ds = n['sharpe'] - base[1.0]['sharpe']; dd2 = d2['sharpe'] - base[2.0]['sharpe']
                yb = sum(1 for y in YEARS if n['years'][y] > base[1.0]['years'][y])
                checks = dict(sharpe=ds >= P['dsharpe'], years=yb >= P['years_better'], double_costs=dd2 >= P['double_cost_dsharpe'],
                              nearby=all(x['sharpe'] - base[1.0]['sharpe'] >= P['nearby_dsharpe'] for x in near))
                res = dict(id=a['id'], name=a['name'], kind=a['kind'], target=a['target'], kw=a['kw'], normal=n, double=d2, nearby=near,
                           dsharpe=round(ds, 3), dsharpe_double=round(dd2, 3), years_better=yb, checks=checks, verdict='PASS' if all(checks.values()) else 'fail')
        except Exception as e:
            res = dict(id=a['id'], name=a['name'], verdict='error', error=repr(e))
        json.dump(res, open(f, 'w'), indent=1, default=str); log('  ->', res['verdict'], res.get('dsharpe', ''))
    summarise(base)

def summarise(base):
    rows = [json.load(open(f"{ADJ_DIR}/{a['id']}.json")) for a in adj.A if os.path.exists(f"{ADJ_DIR}/{a['id']}.json")]
    surv = [r['id'] for r in rows if r['verdict'] == 'PASS']
    json.dump(dict(baseline=base[1.0]['sharpe'], baseline_double=base[2.0]['sharpe'], tested=len(rows), survivors=surv), open(OUT + '/summary.json', 'w'), indent=1)
    L = ['# Adjustment test results (Jul 2021 - Dec 2024, lockbox closed)', '',
         f"Baseline Sharpe {base[1.0]['sharpe']} (double costs {base[2.0]['sharpe']}), {base[1.0]['R']}R. Tested {len(rows)} of {len(adj.A)}. **Survivors: {', '.join(surv) or 'none'}**", '',
         '| id | adjustment | dSharpe | dSharpe 2x cost | years better | nearby ok | verdict |', '|---|---|---|---|---|---|---|']
    for r in sorted(rows, key=lambda r: -r.get('dsharpe', -9)):
        if r['verdict'] == 'reported': continue
        ch = r.get('checks', {})
        L.append(f"| {r['id']} | {r['name']} | {r.get('dsharpe', '')} | {r.get('dsharpe_double', '')} | {r.get('years_better', '')} | {ch.get('nearby', '')} | {r['verdict']} |")
    L += ['', '## Risk levels (reported, not pass/fail)', '', '| risk | a year | worst drop | halving chance |', '|---|---|---|---|']
    for r in rows:
        if r['verdict'] == 'reported': x = r['report']; L.append(f"| {x['risk']}% | {x['a_year']}% | {x['worst_drop']}% | {x['halving_chance']}% |")
    open(OUT + '/SUMMARY.md', 'w').write('\n'.join(L) + '\n'); log('summary written,', len(surv), 'survivors')

def lockbox_mode():
    surv = json.load(open(OUT + '/summary.json'))['survivors']; A = {a['id']: a for a in adj.A}
    base = {cx: score(book(cx), cx) for cx in (1.0, 2.0)}; res = dict(window=[MONTHS[0], MONTHS[-1]], baseline=base[1.0], baseline_double=base[2.0], results={})
    for i in surv:
        a = A[i]; n = run_one(a, a['kw'], 1.0); d2 = run_one(a, a['kw'], 2.0)
        ok = n['sharpe'] > base[1.0]['sharpe'] and d2['sharpe'] > base[2.0]['sharpe']
        res['results'][i] = dict(name=a['name'], normal=n, double=d2, verdict='KEEP' if ok else 'OUT'); log(i, res['results'][i]['verdict'])
    json.dump(res, open(OUT + '/lockbox.json', 'w'), indent=1)

if __name__ == '__main__':
    lockbox_mode() if MODE == 'lockbox' else test_mode()
