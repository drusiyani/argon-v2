"""ROUND 2 pre-registered adjustments + the 2010-2020 lockbox rules. Committed BEFORE any round-2 test code exists.
research/ADJUSTMENTS2.md is generated from this file. Reviewed by a 5-member council (statistician, risk manager,
execution trader, sceptic, methodologist) on 28 Oct 2026; their changes are applied."""

BASELINE = ('The final v2 book (Amendment 3): QuantLab (NQ, walk-forward, skips FOMC days) + noise band (NQ) + ATR band (NQ) '
            '+ expiry reversal (NQ + ES), 1R per trade each, 0.75% risk, no daily loss limit.')
TEST_WINDOW = ('2021-07', '2026-09')          # all already seen
LOCKBOX = ('2011-01', '2020-12')              # never seen; Jun-Dec 2010 is warm-up only (indicators + walk-forward history)

PASS = dict(dsharpe=0.10, years_better=4, years_total=6, vol_matched_years=True, double_cost_dsharpe=0.05, nearby_dsharpe=0.05)
LOCKBOX_PASS = dict(dsharpe=0.03, double_cost_dsharpe=0.0)   # vs the baseline on 2011-2020, both must hold
B0_PASS = dict(sharpe=0.40, double_cost_sharpe=0.0, positive_years=6, of_years=10)

RULES = [
 'Test window: Jul 2021 - Sep 2026. Lockbox: Jan 2011 - Dec 2020, opened ONCE, for the survivors AND the base book (B0), in a single run whose results are written to a file before anyone reads them.',
 f'Pass marks (all must hold): Sharpe at least +{PASS["dsharpe"]:.2f} over the baseline; better than the baseline in at least {PASS["years_better"]} of the {PASS["years_total"]} years, '
 'with each year compared at the SAME volatility (the adjustment\'s monthly series is rescaled to the baseline\'s standard deviation first: this fixes round 1\'s risk-parity flaw); '
 f'at least +{PASS["double_cost_dsharpe"]:.2f} better at double costs; every nearby setting at least +{PASS["nearby_dsharpe"]:.2f} better.',
 f'Lockbox pass: Sharpe at least +{LOCKBOX_PASS["dsharpe"]:.2f} over the baseline at normal costs AND better at double costs. Fail = out, no retries.',
 f'B0 (the base book itself on 2011-2020): passes if Sharpe >= {B0_PASS["sharpe"]}, Sharpe > 0 at double costs, and positive in at least {B0_PASS["positive_years"]} of {B0_PASS["of_years"]} years. '
 'IF B0 FAILS, NOTHING CHANGES: the book still goes live on 1 Jan 2027 and the write-up says so.',
 'Costs are real tick-based costs (NQ 0.75, ES 0.5 points a round trip, same slippage rules). NQ was ~2,000 in 2010 vs ~20,000 now, so costs in R were 5-10x heavier then. '
 'Results at real costs are what count; a version with costs scaled to the price level is reported for information only and cannot rescue a fail.',
 'Data rule (both windows): skip any day missing more than 10% of its 9:30-16:00 minutes (checked on timestamps only: removes 0 lockbox days); half days (<=300 session minutes) are skipped by the loader as always (78 in the lockbox).',
 'FOMC days 2010-2020 from research/calendar_hist.py (Fed historical pages). Before Mar 2013 be flat by 12:25pm; 3 Mar 2020 by 9:55am; otherwise 1:55pm.',
 'Walk-forward strategies in the lockbox re-pick only from earlier lockbox months (warm-up Jun-Dec 2010), never from 2021+.',
 'Holiday = a weekday with no session or a session of <=300 minutes (derived from the data; holidays are known in advance in real life).',
 'Every "nearby" setting below is fixed now. Trials this round: 17 adjustments + 32 nearby settings, each also at double costs.']

A = []
def add(i, name, kind, kw, nearby, note=''):
    A.append(dict(id=i, name=name, kind=kind, kw=kw, nearby=nearby, note=note))

# ---- balancing
add('R01', 'Risk parity: weight = 1/stdev of each strategy\'s last 12 months, average weight 1', 'port', dict(rule='parity', look=12), [dict(look=9), dict(look=15)])
add('R02', 'Risk parity, 6 months', 'port', dict(rule='parity', look=6), [dict(look=4), dict(look=9)])
add('R03', 'Risk parity 12 months, weights capped 0.5-2', 'port', dict(rule='parity', look=12, lo=0.5, hi=2.0), [dict(look=12, lo=0.67, hi=1.5), dict(look=12, lo=0.33, hi=3.0)])
add('R04', 'Volatility target for the whole book', 'port', dict(rule='voltarget', look=6, cap=1.5, floor=0.5),
    [dict(look=3, cap=1.5, floor=0.5), dict(look=12, cap=1.5, floor=0.5)],
    'scale = (expanding median of past monthly stdev, min 12 months) / (stdev of last `look` months), capped at 1.5x and floored at 0.5x')
add('R05', 'Equal risk per strategy per month', 'port', dict(rule='eqcount', look=6, lo=0.25, hi=4.0), [dict(look=3, lo=0.25, hi=4.0), dict(look=12, lo=0.25, hi=4.0)],
    'each strategy scaled so its trailing trades-per-month matches the book average, capped 0.25-4x')
# ---- more of what works (ES only, no new markets)
add('S01', 'Add the noise band on ES (walk-forward, same variants)', 'add', dict(strat='noiseband', sym='ES', w=1.0), [dict(w=0.75), dict(w=1.25)])
add('S02', 'Add the ATR band on ES', 'add', dict(strat='atrband', sym='ES', w=1.0), [dict(w=0.75), dict(w=1.25)])
# ---- cheaper execution (worst-case fill model)
add('X01', 'QuantLab enters with a limit at the 9:35 open', 'strat', dict(strat='quantlab', limit_ticks=0), [dict(limit_ticks=-1), dict(limit_ticks=1)],
    'fills only if the 9:35 minute trades 1 full tick through the limit; otherwise market at the 9:36 open + 2 ticks. Worst case assumed inside the minute.')
add('X02', 'Expiry enters with a limit at the 9:31 open', 'strat', dict(strat='expiry', limit_ticks=0), [dict(limit_ticks=-1), dict(limit_ticks=1)],
    'same fill rule; fallback market at the 9:32 open + 1 tick')
# ---- less luck in the monthly re-pick
add('W01', 'QuantLab trades its top 2 variants at half size each', 'strat', dict(strat='quantlab', topk=2), [dict(topk=3)])
add('W02', 'Noise band trades its top 2 variants at half size each', 'strat', dict(strat='noiseband', topk=2), [dict(topk=3)])
add('W03', 'Re-pick looks back 12 months; if the best variant did not break even, use the default', 'strat', dict(strat='both', look=12, fallback=True),
    [dict(look=9, fallback=True), dict(look=15, fallback=True)], 'defaults: QuantLab candle stop + EMA exit; noise band 30 min, 1.0x band, VWAP stop')
# ---- the two most similar strategies
add('P01', 'Noise band + ATR band: if one is already open in the same direction, the later one enters at half size', 'port', dict(rule='pairhalf', size=0.5), [dict(size=0.33), dict(size=0.67)])
# ---- calendar (merged per the council)
add('C01', 'Skip days next to market holidays and 20 Dec - 2 Jan', 'port', dict(rule='calendar', start='12-20', end='01-02'), [dict(start='12-22', end='01-02'), dict(start='12-15', end='01-03')])
# ---- gap days (one test only; the half-size version was dropped as a near-copy of a round-1 failure)
add('G01', 'QuantLab skips days whose overnight gap is bigger than 1x daily ATR', 'strat', dict(strat='quantlab', gap_atr=1.0), [dict(gap_atr=0.75), dict(gap_atr=1.25)],
    'gap = 9:30 open vs previous 16:00 close; ATR = 14 previous sessions')
# ---- exits
add('E01', 'ATR band re-picks its exit monthly: no trail / 0.5x ATR trail / 1x ATR trail', 'strat', dict(strat='atrband', exitpick=(None, 0.5, 1.0), look=6),
    [dict(look=3), dict(look=12)])
add('E02', 'Everything flat 15:45 instead of 15:55 (avoids the 3:50pm order-flow burst)', 'multi', dict(flat=945), [dict(flat=940), dict(flat=950)])

DROPPED = ['Early-close days (already skipped by the loader)', 'QuantLab half size on big-gap days (near-copy of a round-1 failure)',
           'Daily loss limits, pullback/delayed entries, QuantLab filters, other markets (failed in round 1 or ruled out)']

def markdown():
    L = ['# Argon v2: round 2 pre-registered adjustments + the 2010-2020 lockbox', '',
         f'{len(A)} adjustments, committed **before any round-2 test code exists**. Reviewed by a 5-member council (statistician, risk manager, execution trader, sceptic, methodologist).', '',
         f'**Baseline:** {BASELINE}', '', '## Rules (fixed now)', ''] + [f'- {r}' for r in RULES] + ['', '## Adjustments', '', '| id | adjustment | settings | nearby | note |', '|---|---|---|---|---|']
    for a in A:
        nb = '; '.join(str(x) for x in a['nearby']) if a['nearby'] else 'n/a'
        L.append(f"| {a['id']} | {a['name']} | `{a['kw']}` | {nb} | {a['note']} |")
    L += ['', '## Dropped after review', ''] + [f'- {d}' for d in DROPPED] + ['', '## Pre-commit checks (timestamps and counts only, no prices)', '',
          '- Lockbox: 22 files, 2010-06-07 to 2020-12-31, sha256 in data/lockbox2010/MANIFEST.json, no duplicate minutes, symbol correct.',
          '- 2,711 sessions per market; 0 days fail the 10% rule; 78 half days; first bar 9:30 New York on every session (DST correct); 4 rolls a year.',
          '- 48 full-closure weekday holidays found (incl. Hurricane Sandy, 29 Oct 2012).',
          '- FOMC: the engine calendar only covered 2021+, which would have silently broken the FOMC rules in the lockbox. Fixed: 88 decision days in research/calendar_hist.py.',
          '- Nothing outside a lockbox run reads data/lockbox2010/.']
    return '\n'.join(L) + '\n'

if __name__ == '__main__':
    import os
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ADJUSTMENTS2.md'), 'w').write(markdown())
    print(len(A), 'adjustments,', sum(len(a['nearby']) for a in A), 'nearby')
