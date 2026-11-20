"""Export the main book (the plain package at 0.5% per rules trade, Amendment 13; G3 shown as the shadow) for the website: docs/data/book.json (curves, headline
numbers) and docs/data/cal/{year}.json (every backtest day: account return, Nasdaq move, each trade and the shadow G3's take/skip call).
Needs the local analysis caches, so it is run by hand after a research change, not by the nightly build."""
import os
A = os.path.dirname(os.path.abspath(__file__)); s29 = open(f'{A}/batch29.py').read()
exec(s29.split('# ---------------------------------------------------------------- U1')[0])
OUT = os.path.join(os.path.dirname(A), 'docs', 'data'); os.makedirs(os.path.join(OUT, 'cal'), exist_ok=True)
K = 1.0                                                      # rules weight 0.5 (Amendment 13)
NM = {'quantlab': 'Opening Drive', 'noiseband': 'Noise Breakout', 'atrband': 'Range Breakout', 'expiry': 'Expiry Reversal'}   # display names (engine/names.py)
book = dict(label='Plain package, 0.5% risk per rules trade (Amendment 13)', eras={}, curve=[], nasdaq=[], g3=[])
cal = collections.defaultdict(dict); eq = eqn = eqg = 1e5; last_m = None
for e in ('lockbox2010', 'databento'):
    q = Q[e]; z = E[e]['z']; days = E[e]['days']; w = np.ones(len(q['tr'])) * K
    r = ret2(e, w); rg = ret2(e, WG3[e] * K); nq = np.array([z['ret'][d] for d in days])
    h = full(r); hg = full(rg); hn = full(nq)
    book['eras'][e] = dict(label='2021–26' if e == 'databento' else '2010–20', start=days[0], end=days[-1], book=h, g3_shadow=hg, nasdaq=hn,
                           g3_skip_share=round(1 - float(np.mean(WG3[e][q['mom']] > 0)), 3))
    byday = collections.defaultdict(list)
    for k, t in enumerate(q['tr']):
        kept = bool(WG3[e][k] > 0) if q['mom'][k] else True
        byday[int(q['day'][k])].append([NM.get(t['strat'], t['strat']), 1 if t['side'] in (1, 'long') else -1, int(t['entry_min']), int(t['exit_min']),
                                        round(float(q['nr'][k]), 2), int(kept), t.get('sym', 'NQ')])
    for i, d in enumerate(days):
        eq *= 1 + r[i]; eqn *= 1 + nq[i]; eqg *= 1 + rg[i]
        cal[d[:4]][d] = dict(r=round(100 * float(r[i]), 3), nq=round(100 * float(nq[i]), 2), t=sorted(byday.get(i, []), key=lambda x: x[2]))
        if d[:7] != last_m:
            book['curve'].append([d[:7], round(eq)]); book['nasdaq'].append([d[:7], round(eqn)]); book['g3'].append([d[:7], round(eqg)]); last_m = d[:7]
        else: book['curve'][-1][1] = round(eq); book['nasdaq'][-1][1] = round(eqn); book['g3'][-1][1] = round(eqg)
db = E['databento']['days']; m26 = np.array([d >= '2026-01-01' for d in db]); r26 = ret2('databento', np.ones(len(Q['databento']['tr'])) * K)[m26]; e26 = np.cumprod(1 + r26)
book['y2026'] = dict(ret=round(100 * (float(e26[-1]) - 1), 1), worst_drop=round(100 * float((e26 / np.maximum.accumulate(np.r_[1.0, e26])[1:] - 1).min()), 1), to=db[-1])
book['honest'] = dict(note='Single backtest run, mostly in-sample, not blind (~299 trials). Batch 34: after counting every trial, G3\'s gain over this package is not proven, so the simpler package is the main book and G3 runs beside it as a test.',
                      trials=299)
json.dump(book, open(os.path.join(OUT, 'book.json'), 'w'), separators=(',', ':'), default=lambda o: o.item() if hasattr(o, 'item') else str(o))
for y, D in cal.items(): json.dump(D, open(os.path.join(OUT, 'cal', f'{y}.json'), 'w'), separators=(',', ':'))
json.dump(sorted(cal), open(os.path.join(OUT, 'cal', 'years.json'), 'w'))
json.dump({d: v['r'] for y in sorted(cal) for d, v in cal[y].items()}, open(os.path.join(OUT, 'book_daily.json'), 'w'), separators=(',', ':'))   # main book's daily % for the chart
print('book', {e: (v['book']['cagr_pct'], v['book']['worst_drop_pct']) for e, v in book['eras'].items()}, book['y2026'], 'years', sorted(cal))
