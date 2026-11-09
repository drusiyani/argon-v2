"""Argon live paper trading: the OFFICIAL book (Task 1, council-approved in research/COUNCIL_LIVE.md).

Every night after the close this runs the exact backtest code (engine/portfolio.py -> research/common.py) on Databento
1-minute data, books every finished session since the last run, and appends it to an append-only, hash-chained ledger.
No separate "live version" of any strategy exists.

Order of every run:
  1. kill switch (data/KILL): if present, book nothing, say why, alert.
  2. ledger chain check: every entry's hash and its link to the previous entry.
  3. replay check: every booked day is rebuilt from scratch with today's code and data and must match the ledger exactly.
     A mismatch (a code change or a Databento revision) halts the book and alerts. The ledger is never rewritten.
  4. data gate: a session is only booked when all four markets' data reaches past 16:00 New York on that day.
  5. book every missed session in order, then the position check (after the close every strategy must be flat).

Money: micro contracts (MNQ $2/pt, MES $5/pt), rounded DOWN at 1% of the account, account compounding in dollars day by day.
Costs: the research costs in points (official) and twice that (the double-cost ledger alongside).
Books: 'official' from 1 Jan 2027 (data/ledger/) and 'practice' from 16 Nov 2026 (data/ledger_practice/).
Usage: python engine/live.py [official|practice]     (default: practice before 2027, official after)"""
import os, sys, json, math, hashlib, subprocess, collections, datetime as dt, statistics as stt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'engine'))
import portfolio as P
c = P.c
from zoneinfo import ZoneInfo
NY = ZoneInfo('America/New_York')

BOOKS = dict(official=dict(start='2027-02-01', folder='data/ledger'), practice=dict(start='2026-11-16', folder='data/ledger_practice'))
START_USD = 100000.0
MICRO = {'NQ': ('MNQ', 2.0), 'ES': ('MES', 5.0)}        # micro contract and dollars per index point
MAX_CONTRACTS = 200                                       # sanity cap per trade (council point 6)
MARKETS = ('NQ', 'ES', 'YM', 'RTY')                       # the data gate needs all four (rolls come from their shared days)
BAND = os.path.join(ROOT, 'research', 'results', 'live_band.json')
COMPARED = ('date', 'status', 'equity_start', 'equity_end', 'trades', 'skipped')    # what the replay check compares

def hm(m): return f'{m // 60:02d}:{m % 60:02d}'
def tid(t): return f"{t['strat']}|{t['sym']}|{t['date']}|{t['entry_min']}|{t['variant']}"
def r6(x): return round(float(x), 6)

def contracts(t, equity, risk_pct):
    """Whole micros, rounded DOWN, so the money at risk is at most risk_pct of the account."""
    ppt = MICRO[t['sym']][1]
    return min(MAX_CONTRACTS, int(math.floor(equity * risk_pct / 100 / (t['risk_pts'] * ppt) + 1e-9)))

def book_day(d, trades, skipped_cost, equity, cx, risk_pct, status):
    out, skipped, pnl = [], [], 0.0
    for t in sorted(trades, key=tid):
        n = contracts(t, equity, risk_pct); sym, ppt = MICRO[t['sym']][0], MICRO[t['sym']][1]
        R = t['gross'] - cx * t['cost']
        if n < 1: skipped.append(dict(id=tid(t), reason='size rounds to 0 micros (risk too wide for 1% of the account)', R_rules=r6(R))); continue
        pts = t['gross'] * t['risk_pts'] - cx * c.COST[t['sym']]
        usd = round(n * ppt * pts, 2)
        out.append(dict(id=tid(t), strategy=t['strat'], market=t['sym'], contract=sym, variant=t['variant'],
                        side='long' if t['side'] == 1 else 'short', entry_time=hm(t['entry_min']), exit_time=hm(t['exit_min']),
                        entry=r6(t['entry']), stop=r6(t['stop']), exit=r6(t['exit']), risk_pts=r6(t['risk_pts']),
                        contracts=n, risk_usd=round(n * ppt * t['risk_pts'], 2), R=r6(R),
                        usd_gross=round(n * ppt * t['gross'] * t['risk_pts'], 2), usd_cost=round(n * ppt * cx * c.COST[t['sym']], 2), usd=usd))
        pnl += usd
    for t in sorted(skipped_cost, key=tid):
        skipped.append(dict(id=tid(t), reason=f"cost rule: costs {t['cost']:.3f}R > {P.CONFIG['cost_cap_R']}R", R_rules=r6(t['gross'] - cx * t['cost'])))
    return dict(date=d, status=status, equity_start=round(equity, 2), equity_end=round(equity + pnl, 2), trades=out, skipped=skipped)

def ehash(e): return hashlib.sha256(json.dumps({k: v for k, v in e.items() if k != 'hash'}, sort_keys=True).encode()).hexdigest()

def read(path):
    if not os.path.exists(path): return []
    return [json.loads(x) for x in open(path) if x.strip()]

def verify_chain(entries):
    prev = '0' * 64
    for i, e in enumerate(entries):
        if e.get('seq') != i: return f'entry {i} has seq {e.get("seq")}'
        if e.get('prev_hash') != prev: return f'entry {i} ({e.get("date")}) does not link to the entry before it'
        if ehash(e) != e.get('hash'): return f'entry {i} ({e.get("date")}) was edited after it was written'
        prev = e['hash']
    return None

def commit():
    s = os.environ.get('GITHUB_SHA')
    if s: return s[:12]
    try: return subprocess.run(['git', '-C', ROOT, 'rev-parse', '--short=12', 'HEAD'], capture_output=True, text=True).stdout.strip() or 'unknown'
    except Exception: return 'unknown'

# ---------------------------------------------------------------- sessions and the data gate
def sessions():
    """date -> regular-session minutes, for every day NQ traded 9:30-16:00 New York."""
    T, O, H, L, C, n, mins, days, wd = c.prep('NQ'); cnt = collections.Counter(days[i] for i in range(n) if 570 <= mins[i] < 960)
    return dict(sorted(cnt.items()))

def last_ts():
    M1, _ = c.m1(); return {s: int(M1[s][0][-1]) for s in MARKETS if s in M1}

def complete(d, lts):
    end = dt.datetime.combine(dt.date.fromisoformat(d), dt.time(16, 0), NY).timestamp()
    return all(lts.get(s, 0) >= end for s in MARKETS)

def status_of(n):
    if n <= 300: return 'half day: no trading'
    if n <= 350: return 'thin data: skipped by the data rule'
    return 'booked'

# ---------------------------------------------------------------- the ledger build (pure: same code + same data = same ledger)
def build(days, cx, risk_pct):
    """Ledger bodies for `days` (in order), starting from START_USD."""
    sk = []; tr = P.book(cx, skipped=sk); by = collections.defaultdict(list); bys = collections.defaultdict(list)
    for t in tr: by[t['date']].append(t)
    for t in sk: bys[t['date']].append(t)
    S = sessions(); eq = START_USD; out = []
    for d in days:
        st = status_of(S.get(d, 0))
        e = book_day(d, by.get(d, []) if st == 'booked' else [], bys.get(d, []) if st == 'booked' else [], eq, cx, risk_pct, st)
        eq = e['equity_end']; out.append(e)
    return out, tr

def body(e): return {k: e[k] for k in COMPARED}

def open_positions(entries):
    """After the close every strategy is flat by 15:55. A trade ending at or after 16:00 means something is wrong."""
    return [t['id'] for e in entries for t in e['trades'] if t['exit_time'] >= '16:00']

# ---------------------------------------------------------------- expected vs actual (pre-registered band, Amendment 6)
def band_check(entries):
    if not os.path.exists(BAND): return None
    B = json.load(open(BAND)); mR = collections.OrderedDict()
    for e in entries:
        if e['status'] != 'booked': continue
        mR.setdefault(e['date'][:7], 0.0)
        mR[e['date'][:7]] += sum(t['R'] for t in e['trades']) + sum(s['R_rules'] for s in e['skipped'] if s['reason'].startswith('size'))
    today = dt.datetime.now(NY).date().isoformat()[:7]
    done = [m for m in mR if m < today]; cur = sum(mR[m] for m in done); k = len(done)
    res = dict(rule=B['rule'], months_done=k, R_done=round(cur, 2), month_R={m: round(v, 2) for m, v in mR.items()})
    if 1 <= k <= 12:
        lo, mid, hi = B['bands'][str(k)]['p5'], B['bands'][str(k)]['p50'], B['bands'][str(k)]['p95']
        res.update(band=[lo, hi], median=mid, verdict='consistent with backtest' if lo <= cur <= hi else ('below the backtest range' if cur < lo else 'above the backtest range'))
    elif k > 12: res.update(verdict='past the 12-month band: judge the full year', band=None)
    else: res.update(verdict='no full month yet', band=None)
    return res

# ---------------------------------------------------------------- daily regime label (extra d)
def regime(days):
    D, dl, _ = c.daily('NQ'); vix = {}
    try:
        import daytype
        for t, o, h, l, cl in daytype.chart('%5EVIX', '2y', '1d'): vix[dt.datetime.fromtimestamp(t, NY).date().isoformat()] = cl
    except Exception as e: print('VIX unavailable, regime uses the range only:', e)
    out = {}; vk = sorted(vix)
    for d in days:
        if d not in D: continue
        k = dl.index(d)
        if k < 20: continue
        x = D[d]; rng = x['h'] - x['l']; avg = stt.mean(D[dl[j]]['h'] - D[dl[j]]['l'] for j in range(k - 20, k)); ratio = rng / avg if avg else 1
        v = vix.get(d); past = [vix[q] for q in vk if q <= d][-252:]
        pct = round(100 * sum(1 for y in past if y <= v) / len(past)) if v is not None else None
        trend = rng > 0 and abs(x['c'] - x['o']) >= 0.6 * rng
        lab = 'trending' if trend else ('calm' if ratio < 0.8 and (pct is None or pct < 50) else 'choppy')
        out[d] = dict(label=lab, range_ratio=round(ratio, 2), vix=v, vix_pct=pct, trend_day=int(trend))
    return out

# ---------------------------------------------------------------- the run
def run(name=None, now=None, root=None):
    now = now or dt.datetime.now(NY)
    name = name or ('practice' if now.date() < dt.date(2027, 2, 1) else 'official')
    B = BOOKS[name]; folder = os.path.join(root or ROOT, B['folder']); os.makedirs(folder, exist_ok=True)
    paths = {1.0: os.path.join(folder, 'ledger.jsonl'), 2.0: os.path.join(folder, 'ledger_2x.jsonl')}
    stat = dict(book=name, start=B['start'], run_at=now.isoformat(timespec='seconds'), code=commit(), checks={})
    alerts = []
    def finish(state, code=0):
        stat['state'] = state; stat['alerts'] = alerts
        json.dump(stat, open(os.path.join(folder, 'status.json'), 'w'), indent=1)
        if root: print('scratch run:', state); return code       # test/scratch runs: no publishing, no alerts
        publish(name, folder, stat)
        try:
            import alert
            for a in alerts: alert.send(*a)
        except Exception as e: print('alert failed', e)
        print(json.dumps({k: stat[k] for k in ('book', 'state', 'checks')}, default=str)); return code

    # 1. kill switch first
    kill = os.path.join(ROOT, 'data', 'KILL')
    if os.path.exists(kill):
        stat['checks']['kill'] = 'ON: ' + (open(kill).read().strip() or 'no reason given')
        alerts.append(('Argon: kill switch is on', stat['checks']['kill'] + '. Nothing was booked.', 'high')); return finish('stopped by kill switch')
    stat['checks']['kill'] = 'off'
    risk = P.CONFIG['risk_pct']; ledgers = {cx: read(p) for cx, p in paths.items()}

    # 2. chain
    for cx, L in ledgers.items():
        bad = verify_chain(L)
        if bad:
            stat['checks']['chain'] = f'{cx:g}x: {bad}'; alerts.append(('Argon: ledger chain broken', bad, 'urgent')); return finish('halted: chain broken', 2)
    stat['checks']['chain'] = 'ok'

    # 3. sessions to book (in order, stopping at the first incomplete one)
    S = sessions(); lts = last_ts(); booked = [e['date'] for e in ledgers[1.0]]
    last = booked[-1] if booked else ''
    todo = []
    for d in S:
        if d < B['start'] or d <= last: continue
        if dt.date.fromisoformat(d) > now.date() or (d == now.date().isoformat() and now.time() < dt.time(16, 15)): break
        if not complete(d, lts): stat['waiting_for'] = d; break
        todo.append(d)
    stat['data_last_bar_utc'] = {s: dt.datetime.fromtimestamp(v, dt.timezone.utc).strftime('%Y-%m-%d %H:%M') for s, v in lts.items()}

    # 4. rebuild everything from scratch and compare (replay check), then append the new days
    for cx in (1.0, 2.0):
        L = ledgers[cx]; days = [e['date'] for e in L] + todo
        built, _ = build(days, cx, risk)
        for old, new in zip(L, built):
            if body(old) != body(new):
                why = f"{cx:g}x ledger, {old['date']}: today's code and data give a different day than the one booked"
                stat['checks']['replay'] = why; alerts.append(('Argon: replay mismatch, book halted', why, 'urgent'))
                json.dump(dict(date=old['date'], booked=body(old), rebuilt=body(new)), open(os.path.join(folder, 'mismatch.json'), 'w'), indent=1)
                return finish('halted: replay mismatch', 2)
        prev = L[-1]['hash'] if L else '0' * 64
        with open(paths[cx], 'a') as f:
            for e in built[len(L):]:
                e = dict(seq=len(L), **e, code_commit=stat['code'], booked_at=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
                         data_last_bar_utc=stat['data_last_bar_utc'], prev_hash=prev)
                e['hash'] = ehash(e); prev = e['hash']; L.append(e); f.write(json.dumps(e, sort_keys=True) + '\n')
    stat['checks']['replay'] = f'ok ({len(ledgers[1.0]) - len(todo)} days re-derived)'
    stat['booked_now'] = todo

    # 5. position check
    op = open_positions(ledgers[1.0]) + open_positions(ledgers[2.0])
    if op:
        stat['checks']['positions'] = f'MISMATCH: {op}'; alerts.append(('Argon: position mismatch, book halted', f'trades still open after the close: {op}', 'urgent'))
        return finish('halted: position mismatch', 2)
    stat['checks']['positions'] = 'flat (ledger and engine agree: no open trades)'
    L = ledgers[1.0]
    stat.update(last_booked=L[-1]['date'] if L else None, equity=L[-1]['equity_end'] if L else START_USD,
                equity_2x=ledgers[2.0][-1]['equity_end'] if ledgers[2.0] else START_USD, days=len(L),
                trades=sum(len(e['trades']) for e in L), band=band_check(L))

    # extras: regime labels, missed morning calls
    rp = os.path.join(folder, 'regime.json'); reg = json.load(open(rp)) if os.path.exists(rp) else {}
    new = [e['date'] for e in L if e['date'] not in reg]
    if new: reg.update(regime(new)); json.dump(dict(sorted(reg.items())), open(rp, 'w'), indent=1)
    dtp = os.path.join(ROOT, 'data', 'daytype.jsonl'); calls = set()
    if os.path.exists(dtp):
        for ln in open(dtp):
            try: calls.add(json.loads(ln)['date'])
            except Exception: pass
    missed = [d for d in todo if d >= '2026-11-03' and d not in calls and status_of(S.get(d, 0)) == 'booked']
    if missed: alerts.append(('Argon: missed morning call', f'no morning call was saved for {", ".join(missed)}', 'default'))
    stat['missed_morning_calls'] = missed
    if stat['band'] and stat['band'].get('verdict', '').startswith('below'):
        alerts.append(('Argon: below the backtest range', f"{stat['band']['R_done']}R after {stat['band']['months_done']} months, band {stat['band']['band']}", 'default'))
    return finish('ok' if 'waiting_for' not in stat or todo else 'ok (waiting for data)')

def publish(name, folder, stat):
    """docs/data/ledger.json: the public summary the site and desk read (the full ledgers are public in data/ too)."""
    L = read(os.path.join(folder, 'ledger.jsonl')); L2 = read(os.path.join(folder, 'ledger_2x.jsonl'))
    rp = os.path.join(folder, 'regime.json'); reg = json.load(open(rp)) if os.path.exists(rp) else {}
    out = dict(book=name, generated=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC'), status=stat,
               equity=[[e['date'], e['equity_end']] for e in L], equity_2x=[[e['date'], e['equity_end']] for e in L2],
               head_hash=L[-1]['hash'] if L else None, days=[dict(date=e['date'], status=e['status'], usd=round(e['equity_end'] - e['equity_start'], 2),
               trades=e['trades'], skipped=e['skipped'], regime=reg.get(e['date']), hash=e['hash'][:12], code=e['code_commit']) for e in L[-30:]][::-1],
               ledger_url=f"https://github.com/drusiyani/argon-v2/blob/main/{BOOKS[name]['folder']}/ledger.jsonl")
    try: import public_bars as pb; out['bars'] = bars5({e['date'] for e in L[-30:] if e['trades']}); out['bars_source'] = pb.SOURCE
    except Exception as ex: print('bars for the desk failed:', ex)
    os.makedirs(os.path.join(ROOT, 'docs', 'data'), exist_ok=True)
    json.dump(out, open(os.path.join(ROOT, 'docs', 'data', 'ledger.json'), 'w'), separators=(',', ':'))

def bars5(days):
    """{date: {sym: [[minute, o, h, l, c], ...]}} 5-minute regular-session bars, for the desk's 'why it fired' charts.
    From Yahoo (engine/public_bars.py), never Databento: the licence forbids republishing it. Yahoo only reaches back about
    60 sessions, so bars already published (and marked as Yahoo's) are kept."""
    import public_bars as pb
    try: old = json.load(open(os.path.join(ROOT, 'docs', 'data', 'ledger.json')))
    except Exception: old = {}
    out = {d: v for d, v in (old.get('bars') or {}).items() if d in days} if old.get('bars_source') == pb.SOURCE else {}
    for s in ('NQ', 'ES'):
        for d, b in pb.sessions(s).items():
            if d in days: out.setdefault(d, {})[s] = b
    return out

if __name__ == '__main__':
    arg = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in BOOKS else None
    sys.exit(run(arg))
