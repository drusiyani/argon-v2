"""Argon v2 portfolio (pre-registration Amendment 3): the four strategies that survived, as one book.

  noise band (NQ)  +  ATR band (NQ)  +  options-expiry reversal (NQ + ES), skipping any trade whose cost is over 10% of 1R
  (Amendment 3e, 28 Oct 2026: QuantLab dropped after it showed no edge before costs on 2011-2020; picked by a rule fixed in
  advance in research/variations.py. Was: QuantLab + the three.)
  1% of the account per trade (0.75% until 28 Oct 2026), each strategy 1R per trade, no daily loss limit (it failed with exact timing).

Also runs the SHADOW strategy: the same book with 12-month risk-parity weights (P13). It is pre-registered here to be
judged on live paper results only, and it never changes the main book.

Kill switch: if data/KILL exists, the book is marked stopped and no new live trades are accepted (it says why).
Writes data/portfolio.json, which the site shows. Strategy logic lives in research/common.py (the tested code)."""
import os, sys, json, statistics as stt, collections, datetime as dt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ['ARGON_FULL'] = '1'          # the lockbox has been opened once already; the full history is the public record now
sys.path.insert(0, os.path.join(ROOT, 'research'))
import common as c

CONFIG = dict(risk_pct=1.0, start_usd=100000, daily_loss_limit=None, amendment=3,
              strategies=dict(noiseband={}, atrband={}, expiry={}), cost_cap_R=0.10, dropped=dict(quantlab='Amendment 3e: no edge before costs on 2011-2020'),
              shadow=dict(name='risk parity (12-month)', look=12, judged_on='live paper results from 1 Jan 2027 only'),
              freeze='2026-12-31T23:59:00Z')
GROUPS = ('noiseband', 'atrband', 'expiry')

def book(cx=1.0):
    kw = CONFIG['strategies']; out = []
    out += c.walkforward(c.noiseband('NQ', **kw['noiseband']), cx)
    out += c.atrband('NQ', **kw['atrband'])
    out += c.opex('NQ', **kw['expiry']) + c.opex('ES', **kw['expiry'])
    out = [t for t in out if t['cost'] <= CONFIG['cost_cap_R']]      # cost known at entry: skip trades where costs eat over 10% of 1R
    for t in out: t['w'] = 1.0
    return sorted(out, key=lambda t: (t['date'], t['entry_min']))

def parity(trades, cx, look):
    """Shadow weights: 1 / stdev of each strategy's last `look` months, rescaled so the average weight is 1.
    Uses only months that finished BEFORE the month being traded."""
    gm = collections.defaultdict(lambda: collections.defaultdict(float))
    for t in trades: gm[t['strat']][t['month']] += t['gross'] - cx * t['cost']
    allm = c.months_between('2021-01', max(t['month'] for t in trades)); W = {}
    for i, m in enumerate(allm):
        prev = allm[max(0, i - look):i]
        if len(prev) < look: continue
        inv = {g: 1 / stt.pstdev([gm[g].get(p, 0.0) for p in prev]) for g in GROUPS if stt.pstdev([gm[g].get(p, 0.0) for p in prev]) > 0}
        if not inv: continue
        mu = sum(inv.values()) / len(inv); W[m] = {g: inv.get(g, mu) / mu for g in GROUPS}
    return [dict(t, w=W.get(t['month'], {}).get(t['strat'], 1.0)) for t in trades], W

def curve(trades, months, cx, risk):
    mm = collections.defaultdict(float)
    for t in trades: mm[t['month']] += t['w'] * (t['gross'] - cx * t['cost'])
    s = [mm.get(m, 0.0) for m in months]; eq = CONFIG['start_usd']; pk = eq; dd = 0; pts = []; yrs = collections.OrderedDict(); y0 = {}
    for m, v in zip(months, s):
        y0.setdefault(m[:4], eq); eq *= 1 + v * risk / 100; pk = max(pk, eq); dd = min(dd, eq / pk - 1); pts.append([m, round(eq)]); yrs[m[:4]] = eq
    years = {y: dict(pct=round((e / y0[y] - 1) * 100, 1), usd=round(e - y0[y])) for y, e in yrs.items()}
    return dict(sharpe=round(c.sharpe(s), 2), R=round(sum(s), 1), final=round(eq), a_year=round(((eq / CONFIG['start_usd']) ** (12 / len(s)) - 1) * 100, 1),
                worst_drop=round(dd * 100, 1), losing_months=sum(1 for v in s if v < 0), months=len(s), years=years, equity=pts, monthly_R=[round(v, 2) for v in s])

if __name__ == '__main__':
    killed = os.path.exists(os.path.join(ROOT, 'data', 'KILL'))
    end = max(c.FULL_END, dt.date.today().replace(day=1).isoformat()[:7])
    trades = book(1.0); last = max(t['month'] for t in trades); months = c.months_between(c.FIRST_MONTH, last)
    main = curve(trades, months, 1.0, CONFIG['risk_pct']); dbl = curve(book(2.0), months, 2.0, CONFIG['risk_pct'])
    sh_trades, W = parity(trades, 1.0, CONFIG['shadow']['look']); shadow = curve(sh_trades, months, 1.0, CONFIG['risk_pct'])
    by = collections.Counter(t['strat'] for t in trades if t['month'] >= c.FIRST_MONTH)
    hm = lambda m: f'{m // 60:02d}:{m % 60:02d}'
    recent = [dict(date=t['date'], strategy=t['strat'], symbol=t['sym'], side='long' if t['side'] == 1 else 'short', entry=hm(t['entry_min']), exit=hm(t['exit_min']),
                   R=round(t['gross'] - t['cost'], 2)) for t in trades[-40:]][::-1]
    out = dict(generated=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC'), config=CONFIG, status='stopped by kill switch' if killed else 'ready for paper trading from 1 Jan 2027',
               killed=killed, window=[months[0], months[-1]], main=main, double_costs={k: dbl[k] for k in ('sharpe', 'R', 'final', 'a_year', 'worst_drop')},
               shadow={k: shadow[k] for k in ('sharpe', 'R', 'final', 'a_year', 'worst_drop', 'equity', 'years')}, shadow_weights_latest=W.get(months[-1]),
               trades_by_strategy=dict(by), recent_trades=recent,
               honesty=['Most of this history is in-sample: the strategies and their settings were picked by looking at it.',
                        'Only Jan 2025 - Sep 2026 tested the final adjustment out of sample (Sharpe about 0.65 there).',
                        'Expect live results closer to 2025-26 than 2022-24.'])
    json.dump(out, open(os.path.join(ROOT, 'data', 'portfolio.json'), 'w'), indent=1)
    print('portfolio', main['sharpe'], main['final'], 'shadow', shadow['sharpe'], shadow['final'], 'killed' if killed else '')
