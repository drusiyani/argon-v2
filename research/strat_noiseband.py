"""Rebuilt noiseband strategy with trade-level output (date, entry time, exit time, side, R). Logic lives in common.py.
Run: ARGON_FULL=1 python research/strat_noiseband.py   -> research/results/trades_noiseband.csv (full history, base settings)."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as c
def trades(cx=1.0, **kw):
    if 'noiseband' == 'quantlab': return c.walkforward(c.quantlab('NQ', **kw), cx)
    if 'noiseband' == 'noiseband': return c.walkforward(c.noiseband('NQ', **kw), cx)
    if 'noiseband' == 'atrband': return c.atrband('NQ', **kw)
    return c.opex('NQ', **kw) + c.opex('ES', **kw)
if __name__ == '__main__':
    t = trades(); end = c.FULL_END if c.OPEN else c.TEST_END
    t = [x for x in t if c.FIRST_MONTH <= x['month'] <= end]
    c.write_csv(t, c.ROOT + '/research/results/trades_noiseband.csv')
    ser = c.monthly(t, c.months_between(c.FIRST_MONTH, end))
    print('noiseband', len(t), 'trades', round(sum(ser), 1), 'R', 'Sharpe', round(c.sharpe(ser), 2))
