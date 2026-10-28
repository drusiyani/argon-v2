"""Round 2: test the 17 pre-registered adjustments (research/adjustments2.py) exactly as written.

  python research/run2.py               test window Jul 2021 - Sep 2026 (already seen). Saves results/round2/<id>.json after
                                        EACH test and skips finished ones, so a timed-out run carries on next time.
  python research/run2.py lockbox       the ONE-TIME 2011-2020 lockbox: base book (B0) + the survivors, a single run, written
                                        to results/lockbox2.json before anyone reads it. Refuses to run twice.
Portfolio rules use exact entry/exit minutes (a trade only knows about trades that closed before it opened)."""
import os, sys, json, copy, time, collections, statistics as stt, datetime as dt
MODE = sys.argv[1] if len(sys.argv) > 1 else 'test'
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['ARGON_FULL'] = '1'                                   # 2021-2026 is all seen now
if MODE == 'lockbox': os.environ['ARGON_DATA'] = 'lockbox2010'
sys.path.insert(0, HERE)
import common as c, adjustments2 as adj
OUT = os.environ.get('ARGON_OUT', c.ROOT + '/research/results'); RD = OUT + '/round2'; os.makedirs(RD, exist_ok=True)
if MODE == 'lockbox':
    if os.path.exists(OUT + '/lockbox2.json'): sys.exit('lockbox 2 has already been opened once. No retries.')
    if not os.path.exists(RD + '/summary.json'): sys.exit('run the test window first')
    MONTHS = c.months_between(*adj.LOCKBOX)
else:
    MONTHS = c.months_between(*adj.TEST_WINDOW)
MSET = set(MONTHS); YEARS = sorted({m[:4] for m in MONTHS}); GROUPS = ('quantlab', 'noiseband', 'atrband', 'expiry')
T0 = time.time()
def log(*a): print(f'[{(time.time() - T0) / 60:6.1f}m]', *a, flush=True)

# ---------------------------------------------------------------- the book and its parts
BASE_KW = dict(quantlab=dict(skip_fomc=True), noiseband={}, atrband={}, expiry={})
_RAW = {}
def raw(name, sym, kw):
    key = (name, sym, json.dumps(kw, sort_keys=True, default=str))
    if key not in _RAW:
        f = dict(quantlab=c.quantlab, noiseband=c.noiseband, atrband=c.atrband, expiry=c.opex)[name]
        _RAW[key] = f(sym, **kw)
    return _RAW[key]

def part(name, cx, kw=None, wf=None, sym=None):
    """One strategy's chosen trades. kw = strategy settings, wf = walk-forward settings."""
    kw = dict(BASE_KW[name], **(kw or {})); wf = wf or {}
    if name == 'expiry': t = raw('expiry', 'NQ', kw) + raw('expiry', 'ES', kw)
    elif name == 'atrband' and 'exitpick' in kw:
        k2 = {k: v for k, v in kw.items() if k != 'exitpick'}; t = []
        for vi, tr in enumerate(kw['exitpick']): t += [dict(x, variant=vi) for x in raw('atrband', sym or 'NQ', dict(k2, trail=tr))]
        t = c.walkforward(t, cx, wf.get('look', 6))
    elif name == 'atrband': t = raw('atrband', sym or 'NQ', kw)
    else:
        t = c.walkforward(raw(name, sym or 'NQ', kw), cx, wf.get('look', 6), 'sum', wf.get('topk', 1), wf.get('fallback'))
    return [dict(x, w=x.get('w', 1.0)) for x in t]

def book(cx, over=None, extra=None):
    over = over or {}; out = []
    for g in GROUPS:
        o = over.get(g, {}); out += part(g, cx, o.get('kw'), o.get('wf'))
    for e in (extra or []): out += [dict(x, w=x['w'] * e['w'], strat=e['strat'] + '_' + e['sym']) for x in part(e['strat'], cx, sym=e['sym'])]
    return sorted(out, key=lambda t: (t['date'], t['entry_min'], t['exit_min']))

def R(t, cx): return t['w'] * (t['gross'] - cx * t['cost'])

# ---------------------------------------------------------------- portfolio rules
def sequential(ts, cx, decide):
    days = collections.defaultdict(list)
    for t in ts: days[t['date']].append(t)
    for d in sorted(days):
        acc = []
        for t in sorted(days[d], key=lambda t: t['entry_min']):
            openl = [a for a in acc if a['exit_min'] >= t['entry_min']]
            t['w'] = decide(t, openl)
            if t['w'] > 0: acc.append(t)
    return ts

def monthly_by(ts, cx, key):
    g = collections.defaultdict(lambda: collections.defaultdict(float))
    for t in ts: g[key(t)][t['month']] += R(t, cx)
    return g

def allmonths(ts): return c.months_between(min(t['month'] for t in ts), max(t['month'] for t in ts))

def rule(kw, ts, cx):
    r = kw['rule']; groups = sorted({t['strat'] for t in ts})
    if r == 'parity':
        gm = monthly_by(ts, 1.0, lambda t: t['strat']); am = allmonths(ts); W = {}
        for i, m in enumerate(am):
            prev = am[max(0, i - kw['look']):i]
            if len(prev) < kw['look']: continue
            sd = {g: stt.pstdev([gm[g].get(p, 0.0) for p in prev]) for g in groups}; inv = {g: 1 / v for g, v in sd.items() if v > 0}
            if not inv: continue
            mu = sum(inv.values()) / len(inv); w = {g: inv.get(g, mu) / mu for g in groups}
            if kw.get('lo') is not None: w = {g: min(kw['hi'], max(kw['lo'], x)) for g, x in w.items()}
            W[m] = w
        for t in ts: t['w'] *= W.get(t['month'], {}).get(t['strat'], 1.0)
    elif r == 'voltarget':
        mm = collections.defaultdict(float)
        for t in ts: mm[t['month']] += R(t, 1.0)
        am = allmonths(ts); s = [mm.get(m, 0.0) for m in am]; hist = []; W = {}
        for i, m in enumerate(am):
            if i >= kw['look']:
                sd = stt.pstdev(s[i - kw['look']:i])
                if len(hist) >= 12 and sd > 0: W[m] = max(kw['floor'], min(kw['cap'], stt.median(hist) / sd))
                hist.append(sd)
        for t in ts: t['w'] *= W.get(t['month'], 1.0)
    elif r == 'eqcount':
        cnt = collections.defaultdict(collections.Counter)
        for t in ts: cnt[t['strat']][t['month']] += 1
        am = allmonths(ts); W = {}
        for i, m in enumerate(am):
            prev = am[max(0, i - kw['look']):i]
            if len(prev) < kw['look']: continue
            per = {g: sum(cnt[g][p] for p in prev) / len(prev) for g in groups}; avg = sum(per.values()) / len(per)
            W[m] = {g: (min(kw['hi'], max(kw['lo'], avg / v)) if v > 0 else 1.0) for g, v in per.items()}
        for t in ts: t['w'] *= W.get(t['month'], {}).get(t['strat'], 1.0)
    elif r == 'pairhalf':
        PAIR = ('noiseband', 'atrband')
        sequential(ts, cx, lambda t, op: t['w'] * kw['size'] if t['strat'] in PAIR and t['sym'] == 'NQ' and
                   any(a['strat'] in PAIR and a['strat'] != t['strat'] and a['side'] == t['side'] for a in op) else t['w'])
    elif r == 'calendar':
        T, O, H, L, C, n, mins, days, wd = c.prep('NQ'); cnt = collections.Counter(days[i] for i in range(n) if 570 <= mins[i] < 960)
        sess = sorted(d for d, k in cnt.items() if k > 300)
        lo, hi = dt.date.fromisoformat(sess[0]), dt.date.fromisoformat(sess[-1])
        wk = [lo + dt.timedelta(k) for k in range((hi - lo).days + 1)]; ss = set(sess)
        hol = {d for d in wk if d.weekday() < 5 and d.isoformat() not in ss}
        near = set()
        for h in hol:
            for step in (-1, 1):
                x = h + dt.timedelta(step)
                while x.weekday() >= 5 or (x in hol): x += dt.timedelta(step)
                near.add(x.isoformat())
        def season(d):
            md = d[5:]; return md >= kw['start'] or md <= kw['end']
        for t in ts:
            if t['date'] in near or season(t['date']): t['w'] = 0.0
    else: raise ValueError(r)
    return ts

# ---------------------------------------------------------------- build one configuration
def build(a, kw, cx):
    k = a['kind']; base = a['kw']; kw = dict(base, **kw)
    if k == 'port': return rule(kw, book(cx), cx)
    if k == 'add': return book(cx, extra=[dict(strat=kw['strat'], sym=kw['sym'], w=kw['w'])])
    if k == 'multi': return book(cx, {g: dict(kw=dict(flat=kw['flat'])) for g in ('quantlab', 'noiseband', 'atrband')})
    s = kw['strat']; skw = {x: v for x, v in kw.items() if x in ('limit_ticks', 'gap_atr', 'exitpick')}
    wf = {x: v for x, v in kw.items() if x in ('topk', 'look', 'fallback')}
    if wf.get('fallback'): wf['fallback'] = {'quantlab': 0, 'noiseband': 1}
    if s == 'both': return book(cx, {g: dict(wf=dict(wf, fallback=wf['fallback'][g] if wf.get('fallback') else None)) for g in ('quantlab', 'noiseband')})
    if isinstance(wf.get('fallback'), dict): wf['fallback'] = wf['fallback'][s]
    return book(cx, {s: dict(kw=skw, wf=wf)})

# ---------------------------------------------------------------- scoring
def series(ts, cx):
    mm = collections.defaultdict(float)
    for t in ts:
        if t['month'] in MSET: mm[t['month']] += R(t, cx)
    return [mm.get(m, 0.0) for m in MONTHS]
def years(s): return {y: round(sum(v for m, v in zip(MONTHS, s) if m[:4] == y), 3) for y in YEARS}
def score(ts, cx):
    s = series(ts, cx); return dict(sharpe=round(c.sharpe(s), 3), R=round(sum(s), 2), sd=round(stt.pstdev(s), 4), years=years(s), monthly=[round(v, 3) for v in s])
def vol_matched_years(adj_s, base_s):
    k = (stt.pstdev(base_s) / stt.pstdev(adj_s)) if stt.pstdev(adj_s) > 0 else 1.0
    return years([v * k for v in adj_s])

def grow(s, risk=0.75):
    eq = pk = 1.0; dd = 0
    for v in s: eq *= 1 + v * risk / 100; pk = max(pk, eq); dd = min(dd, eq / pk - 1)
    return round((eq ** (12 / len(s)) - 1) * 100, 1), round(dd * 100, 1)

# ---------------------------------------------------------------- test window
def test_mode():
    P = adj.PASS
    base = {cx: score(book(cx), cx) for cx in (1.0, 2.0)}
    json.dump(dict(window=adj.TEST_WINDOW, normal=base[1.0], double=base[2.0]), open(RD + '/baseline.json', 'w'), indent=1)
    log('baseline', base[1.0]['sharpe'], base[1.0]['R'], '| double', base[2.0]['sharpe'])
    only = set(filter(None, os.environ.get('ONLY', '').split(',')))
    for a in adj.A:
        if only and a['id'] not in only: continue
        f = f"{RD}/{a['id']}.json"
        if os.path.exists(f): continue
        log(a['id'], a['name'])
        try:
            n = score(build(a, {}, 1.0), 1.0); d2 = score(build(a, {}, 2.0), 2.0)
            near = [dict(kw=k, **{x: v for x, v in score(build(a, k, 1.0), 1.0).items() if x != 'monthly'}) for k in a['nearby']]
            vy = vol_matched_years(n['monthly'], base[1.0]['monthly']); yb = sum(1 for y in YEARS if vy[y] > base[1.0]['years'][y])
            ds = n['sharpe'] - base[1.0]['sharpe']; dd2 = d2['sharpe'] - base[2.0]['sharpe']
            checks = dict(sharpe=ds >= P['dsharpe'], years=yb >= P['years_better'], double_costs=dd2 >= P['double_cost_dsharpe'],
                          nearby=all(x['sharpe'] - base[1.0]['sharpe'] >= P['nearby_dsharpe'] for x in near))
            res = dict(id=a['id'], name=a['name'], kw=a['kw'], normal={x: v for x, v in n.items() if x != 'monthly'}, double={x: v for x, v in d2.items() if x != 'monthly'},
                       vol_matched_years=vy, years_better=yb, nearby=near, dsharpe=round(ds, 3), dsharpe_double=round(dd2, 3), checks=checks,
                       verdict='PASS' if all(checks.values()) else 'fail')
        except Exception as e:
            import traceback; res = dict(id=a['id'], name=a['name'], verdict='error', error=traceback.format_exc()[-1500:])
        json.dump(res, open(f, 'w'), indent=1, default=str); log('  ->', res['verdict'], res.get('dsharpe', ''))
    rows = [json.load(open(f"{RD}/{a['id']}.json")) for a in adj.A if os.path.exists(f"{RD}/{a['id']}.json")]; surv = [r['id'] for r in rows if r['verdict'] == 'PASS']
    json.dump(dict(baseline=base[1.0]['sharpe'], baseline_double=base[2.0]['sharpe'], tested=len(rows), survivors=surv,
                   errors=[r['id'] for r in rows if r['verdict'] == 'error']), open(RD + '/summary.json', 'w'), indent=1)
    L = ['# Round 2 results (test window Jul 2021 - Sep 2026)', '', f"Baseline Sharpe {base[1.0]['sharpe']} (double costs {base[2.0]['sharpe']}). **Survivors: {', '.join(surv) or 'none'}**", '',
         '| id | adjustment | dSharpe | dSharpe 2x cost | years better (vol-matched) | nearby ok | verdict |', '|---|---|---|---|---|---|---|']
    for r in sorted(rows, key=lambda r: -r.get('dsharpe', -9)):
        L.append(f"| {r['id']} | {r['name']} | {r.get('dsharpe', '')} | {r.get('dsharpe_double', '')} | {r.get('years_better', '')} | {r.get('checks', {}).get('nearby', '')} | {r['verdict']} |")
    open(RD + '/SUMMARY.md', 'w').write('\n'.join(L) + '\n'); log('done,', len(surv), 'survivors')

# ---------------------------------------------------------------- the one-time lockbox
def lockbox_mode():
    surv = json.load(open(RD + '/summary.json'))['survivors']; A = {a['id']: a for a in adj.A}
    out = dict(window=adj.LOCKBOX, opened=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC'), survivors_tested=surv)
    b1, b2 = book(1.0), book(2.0); n, d2 = score(b1, 1.0), score(b2, 2.0)
    # information only: costs scaled to the price level (NQ/ES were ~5-10x cheaper in points then). Cannot rescue a fail.
    ref = {}; px = {}
    for s in ('NQ', 'ES'):
        D, dl, _ = c.daily(s); px[s] = {d: D[d]['c'] for d in dl}
    ref = {'NQ': 15000.0, 'ES': 4500.0}
    scaled = [dict(t, cost=t['cost'] * px[t['sym']].get(t['date'], ref[t['sym']]) / ref[t['sym']]) for t in b1]
    sc = score(scaled, 1.0)
    pos = sum(1 for y in YEARS if n['years'][y] > 0)
    P = adj.B0_PASS
    out['B0'] = dict(normal={k: v for k, v in n.items() if k != 'monthly'}, double={k: v for k, v in d2.items() if k != 'monthly'},
                     a_year_and_worst_drop_at_075=grow(n['monthly']), positive_years=pos, cost_scaled_info_only={k: v for k, v in sc.items() if k != 'monthly'},
                     verdict='PASS' if n['sharpe'] >= P['sharpe'] and d2['sharpe'] > P['double_cost_sharpe'] and pos >= P['positive_years'] else 'FAIL')
    log('B0', out['B0']['verdict'], n['sharpe'], d2['sharpe'], pos)
    out['results'] = {}
    for i in surv:
        a = A[i]; an = score(build(a, {}, 1.0), 1.0); ad = score(build(a, {}, 2.0), 2.0)
        ok = an['sharpe'] - n['sharpe'] >= adj.LOCKBOX_PASS['dsharpe'] and ad['sharpe'] - d2['sharpe'] > adj.LOCKBOX_PASS['double_cost_dsharpe']
        out['results'][i] = dict(name=a['name'], normal={k: v for k, v in an.items() if k != 'monthly'}, double={k: v for k, v in ad.items() if k != 'monthly'}, verdict='KEEP' if ok else 'OUT')
        log(i, out['results'][i]['verdict'])
    json.dump(out, open(OUT + '/lockbox2.json', 'w'), indent=1)

if __name__ == '__main__':
    lockbox_mode() if MODE == 'lockbox' else test_mode()
