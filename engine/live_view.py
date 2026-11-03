"""Argon live view: UNOFFICIAL (Task 1). The nightly Databento ledger (engine/live.py) is the record; this is only a preview.

Every 5 minutes in the desk loop: takes Yahoo's delayed 1-minute bars for today (NQ=F, ES=F, YM=F, RTY=F), adds them after
the last saved Databento minute, and runs the EXACT same book code (engine/portfolio.py -> research/common.py) on that, in a
temporary folder that mirrors the repo (so not one line of strategy code differs). To let the loaders accept a session
that isn't finished yet, the rest of today is padded with flat bars at the last price; anything those fake bars cause is
thrown away: trades entered after the last real minute are dropped, and trades not finished by it are shown as OPEN.

Why it can disagree with the ledger: Yahoo is delayed about 10 minutes, has gaps, and rolls NQ=F on its own timetable.
Writes docs/data/live_view.json. Usage: python engine/live_view.py [--force]"""
import os, sys, json, gzip, glob, shutil, tempfile, subprocess, urllib.request, datetime as dt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from zoneinfo import ZoneInfo
NY = ZoneInfo('America/New_York'); UTC = dt.timezone.utc
YAHOO = {'NQ': 'NQ%3DF', 'ES': 'ES%3DF', 'YM': 'YM%3DF', 'RTY': 'RTY%3DF'}
OUT = os.path.join(ROOT, 'docs', 'data', 'live_view.json')
BARS = {}
HEAD = 'ts_event,rtype,publisher_id,instrument_id,open,high,low,close,volume,symbol\n'

def yahoo_1m(sym):
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{YAHOO[sym]}?interval=1m&range=2d'
    r = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read())['chart']['result'][0]
    q = r['indicators']['quote'][0]
    return [(t, o, h, l, c, v or 0) for t, o, h, l, c, v in zip(r['timestamp'], q['open'], q['high'], q['low'], q['close'], q['volume']) if None not in (o, h, l, c)]

def tail(sym):
    """Last saved Databento bar: (epoch, instrument id, close)."""
    best = None
    for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'databento', f'{sym}_*.csv.gz'))):
        tag = os.path.basename(f)[len(sym) + 1:-7]
        if not (tag.startswith('d') or tag[:4].isdigit() and int(tag[:4]) >= dt.date.today().year - 1): continue
        last = None
        with gzip.open(f, 'rt') as fh:
            for last in fh: pass
        if last and last[:4].isdigit():
            p = last.split(','); ts = int(dt.datetime.fromisoformat(p[0][:19]).replace(tzinfo=UTC).timestamp())
            if best is None or ts > best[0]: best = (ts, p[3], float(p[7]))
    return best

def make_root(today):
    """A temporary repo: engine/ and research/ are links to the real ones; data/databento holds links to the last two years of
    Databento files plus one Yahoo file per market. Returns (path, info)."""
    tmp = tempfile.mkdtemp(prefix='argon_live_'); os.makedirs(os.path.join(tmp, 'data', 'databento'))
    for d in ('engine', 'research'): os.symlink(os.path.join(ROOT, d), os.path.join(tmp, d))
    info = {}; y = today.year
    for sym in YAHOO:
        for f in glob.glob(os.path.join(ROOT, 'data', 'databento', f'{sym}_*.csv.gz')):
            tag = os.path.basename(f)[len(sym) + 1:-7]
            if tag.startswith('d') or tag[:4].isdigit() and int(tag[:4]) >= y - 1: os.symlink(f, os.path.join(tmp, 'data', 'databento', os.path.basename(f)))
        t0, iid, c0 = tail(sym); bars = [b for b in yahoo_1m(sym) if b[0] > t0]
        sess_end = int(dt.datetime.combine(today, dt.time(15, 59), NY).timestamp())
        real = [b for b in bars if b[0] <= sess_end]; last = real[-1] if real else None
        rows = [(t, o, h, l, c, v) for t, o, h, l, c, v in real]
        if last and dt.datetime.fromtimestamp(last[0], NY).date() == today:
            for t in range(last[0] + 60, sess_end + 60, 60): rows.append((t, last[4], last[4], last[4], last[4], 0))   # padding
        with gzip.open(os.path.join(tmp, 'data', 'databento', f'{sym}_zyahoo.csv.gz'), 'wt') as f:
            f.write(HEAD)
            for t, o, h, l, c, v in rows:
                f.write(f"{dt.datetime.fromtimestamp(t, UTC):%Y-%m-%dT%H:%M:%S}.000000000Z,33,1,{iid},{o},{h},{l},{c},{int(v)},{sym}.v.0\n")
        first = real[0] if real else None
        b5 = []
        for t, o, h, l, c, v in real:
            x = dt.datetime.fromtimestamp(t, NY)
            if x.date() != today or not dt.time(9, 30) <= x.time() < dt.time(16, 0): continue
            m5 = x.hour * 60 + x.minute; m5 -= m5 % 5
            if b5 and b5[-1][0] == m5: b5[-1][2] = max(b5[-1][2], h); b5[-1][3] = min(b5[-1][3], l); b5[-1][4] = c
            else: b5.append([m5, o, h, l, c])
        BARS[sym] = b5
        info[sym] = dict(databento_last=dt.datetime.fromtimestamp(t0, NY).strftime('%Y-%m-%d %H:%M'), yahoo_bars=len(real),
                         last_real=dt.datetime.fromtimestamp(last[0], NY).strftime('%Y-%m-%d %H:%M') if last else None, last_price=last[4] if last else None,
                         gap_pct=round((first[1] / c0 - 1) * 100, 2) if first else None)
    return tmp, info

def child(today, last_min, equity):
    """Runs INSIDE the temporary root (ARGON_ROOT set): the official book code, today's trades only."""
    sys.path.insert(0, os.path.join(os.environ['ARGON_ROOT'], 'engine')); import portfolio as P, live
    d = today.isoformat(); sk = []; tr = [t for t in P.book(1.0, skipped=sk) if t['date'] == d]
    T, O, H, L, C, n, mins, days, wd = P.c.prep('NQ'); lastp = {}
    for s in ('NQ', 'ES'):
        Ts, Os, Hs, Ls, Cs, ns, ms, ds, _ = P.c.prep(s)
        lastp[s] = next((Cs[i] for i in range(ns - 1, -1, -1) if ds[i] == d and ms[i] <= last_min), None)
    out = []
    for t in tr:
        if t['entry_min'] > last_min: continue                       # caused by the padding: never happened
        state = 'closed' if t['exit_min'] <= last_min or last_min >= 955 else 'open'
        n_ = live.contracts(t, equity, P.CONFIG['risk_pct']); ppt = live.MICRO[t['sym']][1]; px = lastp.get(t['sym'])
        R_now = ((px - t['entry']) * t['side'] / t['risk_pts'] - t['cost']) if (state == 'open' and px) else t['gross'] - t['cost']
        out.append(dict(id=live.tid(t), strategy=t['strat'], market=t['sym'], contract=live.MICRO[t['sym']][0], contracts=n_,
                        side='long' if t['side'] == 1 else 'short', entry_time=live.hm(t['entry_min']), entry=round(t['entry'], 2), stop=round(t['stop'], 2),
                        exit_time=live.hm(t['exit_min']) if state == 'closed' else None, exit=round(t['exit'], 2) if state == 'closed' else None,
                        last=px, state=state, R_now=round(R_now, 3), usd_now=round(n_ * ppt * R_now * t['risk_pts'], 2)))
    skipped = [dict(id=live.tid(t), reason='cost rule') for t in sk if t['date'] == d and t['entry_min'] <= last_min]
    print('@@' + json.dumps(dict(trades=out, skipped=skipped)))

def main(force=False):
    now = dt.datetime.now(NY); today = now.date()
    if not force and (now.weekday() >= 5 or not dt.time(9, 30) <= now.time() <= dt.time(16, 30)):
        print('market closed: live view not updated'); return
    st = {}
    for f in ('data/ledger/status.json', 'data/ledger_practice/status.json'):
        p = os.path.join(ROOT, f)
        if os.path.exists(p): st = json.load(open(p)); break
    equity = float(st.get('equity', 100000))
    tmp, info = make_root(today)
    try:
        lr = info['NQ']['last_real']; last_min = int(lr[11:13]) * 60 + int(lr[14:16]) if lr and lr[:10] == today.isoformat() else -1
        if last_min < 570: res = dict(trades=[], skipped=[])
        else:
            env = dict(os.environ, ARGON_ROOT=tmp, ARGON_FULL='1')
            p = subprocess.run([sys.executable, os.path.abspath(__file__), '--child', today.isoformat(), str(last_min), str(equity)], env=env,
                               capture_output=True, text=True, timeout=280)
            line = [x for x in p.stdout.splitlines() if x.startswith('@@')]
            if not line: raise RuntimeError('live view failed: ' + (p.stderr or p.stdout)[-600:])
            res = json.loads(line[0][2:])
        warn = [f"{s}: Yahoo's first bar is {v['gap_pct']}% away from Databento's last close (a different contract month?)" for s, v in info.items() if v['gap_pct'] is not None and abs(v['gap_pct']) > 0.6]
        out = dict(unofficial=True, label='UNOFFICIAL live view (Yahoo, delayed ~10 min). The nightly ledger is the record.', date=today.isoformat(),
                   as_of=now.strftime('%Y-%m-%d %H:%M NY'), last_bar=info['NQ']['last_real'], equity_used=equity, markets=info, warnings=warn,
                   bars={k: v for k, v in BARS.items() if k in ('NQ', 'ES')}, **res)
        os.makedirs(os.path.dirname(OUT), exist_ok=True); json.dump(out, open(OUT, 'w'), indent=1)
        print('live view:', len(res['trades']), 'trades,', sum(t['state'] == 'open' for t in res['trades']), 'open', warn or '')
    finally: shutil.rmtree(tmp, ignore_errors=True)

if __name__ == '__main__':
    if '--child' in sys.argv:
        i = sys.argv.index('--child'); child(dt.date.fromisoformat(sys.argv[i + 1]), int(sys.argv[i + 2]), float(sys.argv[i + 3]))
    else: main('--force' in sys.argv)
