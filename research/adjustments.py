"""The pre-registered adjustment list. research/ADJUSTMENTS.md is generated from this file and both are committed
BEFORE any test runs. run_all.py tests exactly these and nothing else.

kind 'strat': re-run one strategy with these settings (the other three stay at base).
kind 'port' : a portfolio-level rule applied to the base trades with their exact entry/exit times.
kind 'size' : a risk level. Sharpe in R can't change, so these are REPORTED (worst drop, halving chance), not pass/fail.
nearby      : neighbouring settings that must ALSO beat the baseline (None = no numeric setting to move)."""

A = []
def add(i, name, kind, target, kw, nearby=None, why=''):
    A.append(dict(id=i, name=name, kind=kind, target=target, kw=kw, nearby=nearby, why=why))

# ---------------- P: portfolio, netting, loss limits, risk caps, balancing
add('P01', 'Net same-minute opposite orders (cost saving only)', 'port', 'netcost', {}, None,
    'one futures account nets positions; only orders in the same minute (e.g. everyone flat at 3:55) actually save costs')
add('P02', 'Skip a new NQ trade if an opposite NQ position is open', 'port', 'opposite', dict(mode='skip'))
add('P03', 'Half size a new NQ trade if an opposite NQ position is open', 'port', 'opposite', dict(mode='half'))
add('P04', 'Exact-time daily loss limit -2R (realised)', 'port', 'losslimit', dict(L=2.0), [dict(L=1.5), dict(L=2.5)])
add('P05', 'Exact-time daily loss limit -1.5R (realised)', 'port', 'losslimit', dict(L=1.5), [dict(L=1.0), dict(L=2.0)])
add('P06', 'Exact-time daily loss limit -3R (realised)', 'port', 'losslimit', dict(L=3.0), [dict(L=2.5), dict(L=3.5)])
add('P07', 'Daily loss limit -2R counting open risk (worst case incl. open trades)', 'port', 'losslimit', dict(L=2.0, openrisk=True), [dict(L=2.5, openrisk=True), dict(L=3.0, openrisk=True)])
add('P08', 'Daily profit lock: no new trades after +4R realised', 'port', 'profitlock', dict(P=4.0), [dict(P=3.0), dict(P=5.0)])
add('P09', 'Total open-risk cap 2R (skip trades that would exceed it)', 'port', 'riskcap', dict(cap=2.0), [dict(cap=1.5), dict(cap=2.5)])
add('P10', 'Total open-risk cap 3R (skip)', 'port', 'riskcap', dict(cap=3.0), [dict(cap=2.5), dict(cap=3.5)])
add('P11', 'Total open-risk cap 2R (shrink new trade to fit, min 0.25)', 'port', 'riskcap', dict(cap=2.0, scale=True), [dict(cap=1.5, scale=True), dict(cap=2.5, scale=True)])
add('P12', 'Risk parity: weight = 1/stdev of last 6 months', 'port', 'parity', dict(look=6), [dict(look=4), dict(look=9)])
add('P13', 'Risk parity: weight = 1/stdev of last 12 months', 'port', 'parity', dict(look=12), [dict(look=9), dict(look=15)])
add('P14', 'Risk parity 6 months, weights capped 0.5-2', 'port', 'parity', dict(look=6, lo=0.5, hi=2.0), [dict(look=6, lo=0.67, hi=1.5), dict(look=6, lo=0.33, hi=3.0)])
add('P15', 'Weight by trailing 12-month Sharpe (negative = 0)', 'port', 'sharpew', dict(look=12), [dict(look=9), dict(look=15)])
add('P16', 'Kill switch: strategy off while its last 12 months are negative', 'port', 'kill', dict(look=12), [dict(look=9), dict(look=15)])
add('P17', 'Kill switch: strategy off while its last 6 months are negative', 'port', 'kill', dict(look=6), [dict(look=4), dict(look=9)])
add('P18', 'Drawdown control: half size while portfolio is >15R below its peak', 'port', 'ddctl', dict(dd=15.0), [dict(dd=10.0), dict(dd=20.0)])
add('P19', 'Weekly loss limit -5R', 'port', 'weeklimit', dict(L=5.0), [dict(L=4.0), dict(L=6.0)])
add('P20', 'Half size after 3 losing days in a row', 'port', 'streak', dict(n=3), [dict(n=2), dict(n=4)])
add('P21', 'Ensemble: 1.5x ATR band / noise band trades that agree with the day\'s QuantLab side', 'port', 'agree', dict(boost=1.5), [dict(boost=1.25), dict(boost=1.75)])
add('P22', 'Ensemble: skip ATR band / noise band trades against the day\'s QuantLab side', 'port', 'against', dict(mode='skip'))
add('P23', 'Ensemble: half ATR band / noise band trades against the day\'s QuantLab side', 'port', 'against', dict(mode='half'))
add('P24', 'Max 2 open same-direction NQ trades', 'port', 'stack', dict(k=2), [dict(k=1), dict(k=3)])
add('P25', 'Max 3 open NQ trades in any direction', 'port', 'maxopen', dict(k=3), [dict(k=2), dict(k=4)])
add('P26', 'Drop the ES expiry leg', 'port', 'weights', dict(w={'expiry_ES': 0.0}))
add('P27', 'Expiry leg 1.5x weight', 'port', 'weights', dict(w={'expiry': 1.5}), [dict(w={'expiry': 1.25}), dict(w={'expiry': 2.0})])
add('P28', 'QuantLab 0.75x weight', 'port', 'weights', dict(w={'quantlab': 0.75}), [dict(w={'quantlab': 0.6}), dict(w={'quantlab': 0.9})])
add('P29', 'Noise band 1.5x weight', 'port', 'weights', dict(w={'noiseband': 1.5}), [dict(w={'noiseband': 1.25}), dict(w={'noiseband': 1.75})])
add('P30', 'ATR band 1.5x weight', 'port', 'weights', dict(w={'atrband': 1.5}), [dict(w={'atrband': 1.25}), dict(w={'atrband': 1.75})])
add('P31', 'Skip the first Friday of each month (jobs report) for every strategy', 'port', 'skipdays', dict(rule='first_friday'))
add('P32', 'Skip FOMC days entirely for every strategy', 'port', 'skipdays', dict(rule='fomc'))
add('P33', 'Max 4 trades per day across the portfolio', 'port', 'maxday', dict(k=4), [dict(k=3), dict(k=5)])
add('P34', 'Cooldown: no new trade for 30 min after any losing exit', 'port', 'cooldown', dict(m=30), [dict(m=15), dict(m=60)])
add('P35', 'Combo: loss limit -2R + open-risk cap 3R', 'port', 'chain', dict(steps=[('losslimit', dict(L=2.0)), ('riskcap', dict(cap=3.0))]),
    [dict(steps=[('losslimit', dict(L=1.5)), ('riskcap', dict(cap=2.5))]), dict(steps=[('losslimit', dict(L=2.5)), ('riskcap', dict(cap=3.5))])])
add('P36', 'Combo: loss limit -2R + risk parity 6m', 'port', 'chain', dict(steps=[('parity', dict(look=6)), ('losslimit', dict(L=2.0))]),
    [dict(steps=[('parity', dict(look=4)), ('losslimit', dict(L=1.5))]), dict(steps=[('parity', dict(look=9)), ('losslimit', dict(L=2.5))])])
add('P37', 'Priority trio: netting + risk parity 6m + loss limit -2R', 'port', 'chain', dict(steps=[('parity', dict(look=6)), ('losslimit', dict(L=2.0)), ('netcost', {})]),
    [dict(steps=[('parity', dict(look=4)), ('losslimit', dict(L=1.5)), ('netcost', {})]), dict(steps=[('parity', dict(look=9)), ('losslimit', dict(L=2.5)), ('netcost', {})])])
add('V01', 'Noise band + ATR band: max 1 open same-direction trade between them', 'port', 'pairstack', dict(k=1))
add('V02', 'QuantLab: skip long trades on expiry Fridays (expiry is known in advance)', 'port', 'qlexpiry', dict(mode='skip_long'))
add('V03', 'QuantLab: half size on expiry Fridays', 'port', 'qlexpiry', dict(mode='half'))

# ---------------- S: risk level (reported only)
for i, r in (('S01', 0.5), ('S02', 0.75), ('S03', 1.0), ('S04', 1.25)):
    add(i, f'Risk {r}% per trade', 'size', 'risk', dict(risk=r))

# ---------------- Q: QuantLab
Q = 'quantlab'
add('Q01', 'Enter one 5-min bar later (9:40)', 'strat', Q, dict(delay=1), [dict(delay=2)])
add('Q02', 'Enter two 5-min bars later (9:45)', 'strat', Q, dict(delay=2), [dict(delay=1), dict(delay=3)])
add('Q03', 'Pullback limit entry 0.25x first-candle range (by 10:00)', 'strat', Q, dict(pullback=0.25), [dict(pullback=0.15), dict(pullback=0.35)])
add('Q04', 'Pullback limit entry 0.5x first-candle range (by 10:00)', 'strat', Q, dict(pullback=0.5), [dict(pullback=0.4), dict(pullback=0.6)])
add('Q05', 'Concretum pullback: wait for one opposite 5-min bar, then enter (by 10:30)', 'strat', Q, dict(concretum=True))
add('Q06', 'ATR stop 0.075x daily ATR (was 0.10)', 'strat', Q, dict(stop_atr=0.075), [dict(stop_atr=0.06), dict(stop_atr=0.09)])
add('Q07', 'ATR stop 0.125x daily ATR', 'strat', Q, dict(stop_atr=0.125), [dict(stop_atr=0.11), dict(stop_atr=0.14)])
add('Q08', 'Chandelier set 2 / 2.5 / 3', 'strat', Q, dict(chands=(2, 2.5, 3)), [dict(chands=(2, 2.5)), dict(chands=(2.5, 3))])
add('Q09', 'Chandelier set 1.5 / 2 / 3', 'strat', Q, dict(chands=(1.5, 2, 3)), [dict(chands=(1.25, 2, 3)), dict(chands=(1.75, 2, 3))])
add('Q10', 'Chandelier set 2 / 3 / 4', 'strat', Q, dict(chands=(2, 3, 4)), [dict(chands=(2, 3, 3.5)), dict(chands=(2, 3, 4.5))])
add('Q11', 'Time exit 12:00', 'strat', Q, dict(te=720), [dict(te=690), dict(te=750)])
add('Q12', 'Time exit 14:00', 'strat', Q, dict(te=840), [dict(te=810), dict(te=870)])
add('Q13', 'Take half off at +2R', 'strat', Q, dict(partial=2.0), [dict(partial=1.5), dict(partial=2.5)])
add('Q14', 'Take half off at +3R', 'strat', Q, dict(partial=3.0), [dict(partial=2.5), dict(partial=3.5)])
add('Q15', 'Stop to breakeven after +1R', 'strat', Q, dict(be=1.0), [dict(be=0.75), dict(be=1.25)])
add('Q16', 'Stop to breakeven after +2R', 'strat', Q, dict(be=2.0), [dict(be=1.5), dict(be=2.5)])
add('Q17', 'Walk-forward lookback 3 months (was 6)', 'strat', Q, dict(_look=3), [dict(_look=2), dict(_look=4)])
add('Q18', 'Walk-forward lookback 12 months', 'strat', Q, dict(_look=12), [dict(_look=9), dict(_look=15)])
add('Q19', 'Walk-forward picks by Sharpe instead of total R', 'strat', Q, dict(_pick='sharpe'))
add('Q20', 'EMA exit needs 2 closes across', 'strat', Q, dict(confirm=2), [dict(confirm=3)])
add('Q21', 'Use a 10-minute first candle (9:30-9:40), enter 9:40', 'strat', Q, dict(first=10))
add('Q22', 'Candle stops only (3 variants)', 'strat', Q, dict(stops=('candle',)))
add('Q23', 'ATR stops only (3 variants)', 'strat', Q, dict(stops=('atr',)))
add('Q24', 'QuantLab skips FOMC days', 'strat', Q, dict(skip_fomc=True))
add('Q25', 'QuantLab flat 15:50 (was 15:55)', 'strat', Q, dict(flat=950), [dict(flat=945), dict(flat=953)])

# ---------------- N: noise band  (lookback 10/20 NOT included: already seen, 0.63/0.81)
N = 'noiseband'
add('N01', 'Decisions every 15, 30 or 60 min (adds 15)', 'strat', N, dict(freqs=(15, 30, 60)))
add('N02', 'Decisions every 30 min only', 'strat', N, dict(freqs=(30,)))
add('N03', 'Band multipliers 0.8 / 1.0 / 1.5', 'strat', N, dict(mults=(0.8, 1.0, 1.5)), [dict(mults=(0.7, 1.0, 1.5)), dict(mults=(0.9, 1.0, 1.5))])
add('N04', 'Band multipliers 1.0 / 1.25 / 1.5', 'strat', N, dict(mults=(1.0, 1.25, 1.5)), [dict(mults=(1.0, 1.15, 1.5)), dict(mults=(1.0, 1.35, 1.5))])
add('N05', 'VWAP stop only', 'strat', N, dict(stops=('vwap',)))
add('N06', 'First decision 15 min earlier', 'strat', N, dict(start=585))
add('N07', 'No new entries after 14:00 (was 15:30)', 'strat', N, dict(cutoff=840), [dict(cutoff=810), dict(cutoff=870)])
add('N08', 'No new entries after 15:00', 'strat', N, dict(cutoff=900), [dict(cutoff=870), dict(cutoff=915)])
add('N09', 'Need two decisions in a row outside the band', 'strat', N, dict(confirm=True))
add('N10', 'Trailing stop 1.0 band-widths, checked every minute', 'strat', N, dict(trail=1.0), [dict(trail=0.75), dict(trail=1.25)])
add('N11', 'Trailing stop 2.0 band-widths', 'strat', N, dict(trail=2.0), [dict(trail=1.5), dict(trail=2.5)])
add('N12', 'Noise band flat 15:00', 'strat', N, dict(te=900), [dict(te=870), dict(te=930)])
add('N13', 'Noise band flat 13:55 on FOMC days (like the others)', 'strat', N, dict(fomc_flat=True))
add('N14', 'Noise band skips FOMC days', 'strat', N, dict(skip_fomc=True))
add('N15', 'Walk-forward picks by Sharpe', 'strat', N, dict(_pick='sharpe'))
add('N16', 'Walk-forward lookback 12 months', 'strat', N, dict(_look=12), [dict(_look=9), dict(_look=15)])
add('N17', 'Walk-forward lookback 3 months', 'strat', N, dict(_look=3), [dict(_look=2), dict(_look=4)])

# ---------------- A: ATR band  (mult 0.4-0.6, lookback 10-20, 30-min checks NOT included: already seen)
B = 'atrband'
add('A01', 'Trailing stop 0.5x daily ATR', 'strat', B, dict(trail=0.5), [dict(trail=0.4), dict(trail=0.6)])
add('A02', 'Trailing stop 1.0x daily ATR', 'strat', B, dict(trail=1.0), [dict(trail=0.8), dict(trail=1.2)])
add('A03', 'Stop to breakeven after +1R', 'strat', B, dict(be=1.0), [dict(be=0.75), dict(be=1.25)])
add('A04', 'Take half off at +1.5R', 'strat', B, dict(partial=1.5), [dict(partial=1.25), dict(partial=1.75)])
add('A05', 'Take half off at +2.5R', 'strat', B, dict(partial=2.5), [dict(partial=2.0), dict(partial=3.0)])
add('A06', 'One entry per day (no re-entry)', 'strat', B, dict(maxent=1))
add('A07', 'Max 2 entries per day', 'strat', B, dict(maxent=2), [dict(maxent=3)])
add('A08', 'No new entries after 14:00', 'strat', B, dict(cutoff=840), [dict(cutoff=810), dict(cutoff=870)])
add('A09', 'No new entries after 12:00', 'strat', B, dict(cutoff=720), [dict(cutoff=690), dict(cutoff=750)])
add('A10', 'ATR band flat 15:00', 'strat', B, dict(te=900), [dict(te=870), dict(te=930)])
add('A11', 'Stop halfway between open and band', 'strat', B, dict(stopmode='mid'))
add('A12', 'Stop 0.25x ATR from entry', 'strat', B, dict(stopmode='atr25'))
add('A13', 'Concretum pullback: wait for one opposite 1-min candle (max 15 min)', 'strat', B, dict(concretum=True))
add('A14', 'Check every 10 minutes (was 15)', 'strat', B, dict(step=10), [dict(step=5), dict(step=12)])
add('A15', 'ATR band skips FOMC days', 'strat', B, dict(skip_fomc=True))

# ---------------- E: expiry  (9:35 entry and 11:30-12:30 exits NOT included: already seen)
E = 'expiry'
add('E01', 'Wider stop: first-minute range + 0.5x ATR', 'strat', E, dict(stopk=0.5), [dict(stopk=0.4), dict(stopk=0.6)])
add('E02', 'No stop (time exit only)', 'strat', E, dict(nostop=True))
add('E03', 'Only after a gap up', 'strat', E, dict(cond=True))
add('E04', 'Cover at 11:00', 'strat', E, dict(xm=660), [dict(xm=630), dict(xm=690)])
add('E05', 'Quarterly expiries only', 'strat', E, dict(quarterly=True))
add('E06', 'Skip expiries in an FOMC week', 'strat', E, dict(skip_fomc_week=True))

# ---------------- C: clock changes for every strategy at once
add('C01', 'Everything flat 15:50 (was 15:55)', 'multi', None, dict(quantlab=dict(flat=950), noiseband=dict(flat=950), atrband=dict(flat=950)),
    [dict(quantlab=dict(flat=945), noiseband=dict(flat=945), atrband=dict(flat=945)), dict(quantlab=dict(flat=953), noiseband=dict(flat=953), atrband=dict(flat=953))])
add('C02', 'No new entries after 15:00 anywhere', 'multi', None, dict(noiseband=dict(cutoff=900), atrband=dict(cutoff=900)),
    [dict(noiseband=dict(cutoff=870), atrband=dict(cutoff=870)), dict(noiseband=dict(cutoff=915), atrband=dict(cutoff=915))])

PASS = dict(dsharpe=0.10, years_better=3, double_cost_dsharpe=0.05, nearby_dsharpe=0.05)
LOCKBOX = 'Survivors are run ONCE on 2025-01..2026-09. Pass = Sharpe above the baseline at normal AND double costs. Fail = out.'

def markdown():
    L = ['# Argon v2: pre-registered adjustments', '',
         f'{len(A)} adjustments, written down **before any test ran** (this commit\'s timestamp is the proof). '
         'Generated from `research/adjustments.py`; `research/run_all.py` tests exactly these.', '',
         '## Rules (fixed in advance)', '',
         '- **Baseline:** QuantLab (walk-forward, 6 variants) + noise band (walk-forward, 8 variants) + ATR band + expiry (NQ+ES), each 1R per trade, summed.',
         '- **Test window:** Jul 2021 to Dec 2024 (42 months). 2025-01 onward is the **lockbox**, not simulated at all.',
         '- **Same realism as always:** costs NQ 0.75 / ES 0.5 pts, stop slippage, roll days skipped, flat 3:55 (1:55 on FOMC days), monthly re-pick from the previous 6 months.',
         f'- **Pass bars** (all must hold): combo Sharpe at least **+{PASS["dsharpe"]:.2f}** over baseline (raised from +0.05 because of ~100 trials); '
         f'better than baseline in at least **{PASS["years_better"]} of the 4 years** (2021 H2, 2022, 2023, 2024); still at least **+{PASS["double_cost_dsharpe"]:.2f}** better at **double costs**; '
         f'every **nearby setting** at least +{PASS["nearby_dsharpe"]:.2f} better.',
         '- **Risk levels (S)** can\'t change a Sharpe measured in R, so they are reported (yearly return, worst drop, halving chance), not passed or failed.',
         f'- **Lockbox:** {LOCKBOX}',
         '- **Honesty note:** the 4 base strategies and their settings were chosen after seeing 2025-2026, so the lockbox only tests these adjustments. The only clean test of the base portfolio is live from 1 Jan 2027.',
         '- Settings already seen on the full history (noise band lookback 10/20, ATR band mult 0.4-0.6 and 30-min checks, expiry 9:35 / 11:30-12:30) are deliberately **left out**.', '']
    groups = [('P', 'Portfolio: netting, loss limits, risk caps, balancing'), ('V', 'Ensemble / calendar'), ('S', 'Risk level (reported only)'),
              ('Q', 'QuantLab'), ('N', 'Noise band'), ('A', 'ATR band'), ('E', 'Expiry reversal'), ('C', 'Clock changes (all strategies)')]
    for g, title in groups:
        L += [f'## {title}', '', '| id | adjustment | settings | nearby |', '|---|---|---|---|']
        for a in A:
            if a['id'][0] != g: continue
            nb = '; '.join(str(x) for x in a['nearby']) if a['nearby'] else 'n/a'
            L.append(f"| {a['id']} | {a['name']}{(' (' + a['why'] + ')') if a['why'] else ''} | `{a['kw']}` | {nb} |")
        L.append('')
    return '\n'.join(L)

if __name__ == '__main__':
    import os
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ADJUSTMENTS.md'), 'w').write(markdown()); print(len(A), 'adjustments')
