"""Export the main book (G3 at 0.625% per rules trade, Amendment 10) for the website: docs/data/book.json (curves, headline
numbers) and docs/data/cal/{year}.json (every backtest day: account return, Nasdaq move, each trade and G3's take/skip call).
Needs the local analysis caches, so it is run by hand after a research change, not by the nightly build."""
import os
A = os.path.dirname(os.path.abspath(__file__)); s29 = open(f'{A}/batch29.py').read()
exec(s29.split('# ---------------------------------------------------------------- U1')[0])
OUT = os.path.join(os.path.dirname(A), 'docs', 'data'); os.makedirs(os.path.join(OUT, 'cal'), exist_ok=True)
K = 1.25                                                     # rules weight 0.625 = 1.25 x the 0.5 reference
NM = {'quantlab': 'QuantLab', 'noiseband': 'Noise band', 'atrband': 'ATR band', 'expiry': 'Expiry'}
book = dict(label='G3 filter, 0.625% risk per rules trade (Amendment 10)', eras={}, curve=[], nasdaq=[], package=[])
cal = collections.defaultdict(dict); eq = eqn = eqp = 1e5; last_m = None
for e in ('lockbox2010', 'databento'):
    q = Q[e]; z = E[e]['z']; days = E[e]['days']; w = WG3[e] * K
    r = ret2(e, w); rp = ret2(e, np.ones(len(q['tr']))); nq = np.array([z['ret'][d] for d in days])
    h = full(r); hp = full(rp); hn = full(nq)
    book['eras'][e] = dict(label='2021–26' if e == 'databento' else '2010–20', start=days[0], end=days[-1], book=h, package_half=hp, nasdaq=hn,
                           skip_share=round(1 - float(np.mean(WG3[e][q['mom']] > 0)), 3))
    byday = collections.defaultdict(list)
    for k, t in enumerate(q['tr']):
        kept = bool(WG3[e][k] > 0) if q['mom'][k] else True
        byday[int(q['day'][k])].append([NM.get(t['strat'], t['strat']), 1 if t['side'] in (1, 'long') else -1, int(t['entry_min']), int(t['exit_min']),
                                        round(float(q['nr'][k]), 2), int(kept), t.get('sym', 'NQ')])
    for i, d in enumerate(days):
        eq *= 1 + r[i]; eqn *= 1 + nq[i]; eqp *= 1 + rp[i]
        cal[d[:4]][d] = dict(r=round(100 * float(r[i]), 3), nq=round(100 * float(nq[i]), 2), t=sorted(byday.get(i, []), key=lambda x: x[2]))
        if d[:7] != last_m:
            book['curve'].append([d[:7], round(eq)]); book['nasdaq'].append([d[:7], round(eqn)]); book['package'].append([d[:7], round(eqp)]); last_m = d[:7]
        else: book['curve'][-1][1] = round(eq); book['nasdaq'][-1][1] = round(eqn); book['package'][-1][1] = round(eqp)
db = E['databento']['days']; m26 = np.array([d >= '2026-01-01' for d in db]); r26 = ret2('databento', WG3['databento'] * K)[m26]; e26 = np.cumprod(1 + r26)
book['y2026'] = dict(ret=round(100 * (float(e26[-1]) - 1), 1), worst_drop=round(100 * float((e26 / np.maximum.accumulate(np.r_[1.0, e26])[1:] - 1).min()), 1), to=db[-1])
book['honest'] = dict(note='Single backtest run, not blind (~297 trials). Batch 29 jitter test: single-run figures carry about ±3 points (2021–26) and ±1.5 (2010–20) of luck.',
                      trials=297)
json.dump(book, open(os.path.join(OUT, 'book.json'), 'w'), separators=(',', ':'), default=lambda o: o.item() if hasattr(o, 'item') else str(o))
for y, D in cal.items(): json.dump(D, open(os.path.join(OUT, 'cal', f'{y}.json'), 'w'), separators=(',', ':'))
json.dump(sorted(cal), open(os.path.join(OUT, 'cal', 'years.json'), 'w'))
print('book', {e: (v['book']['cagr_pct'], v['book']['worst_drop_pct']) for e, v in book['eras'].items()}, book['y2026'], 'years', sorted(cal))
