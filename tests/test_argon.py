"""Argon's safety net. Pins results we have already checked by hand, so an accidental change (a data bug, a broken loader,
a calendar gap) fails loudly instead of quietly changing the research. Run: pytest -q tests/
If a test fails after a DELIBERATE change, update the pinned value in the same commit and say why in the commit message."""
import os, sys, json, glob, hashlib, re
import pytest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'research')); sys.path.insert(0, os.path.join(ROOT, 'engine'))
os.environ['ARGON_FULL'] = '1'
WINDOW = '2026-09'      # results are pinned up to here, so new monthly data never breaks the tests

# ---------------------------------------------------------------- calendars (fast)
def test_fomc_history_complete():
    import calendar_hist as h, collections
    per = collections.Counter(d[:4] for d in h.FOMC_HIST)
    assert len(h.FOMC_HIST) == 88 and all(per[str(y)] == 8 for y in range(2010, 2021)), per

def test_fomc_exit_times():
    import calendar_hist as h
    assert h.exit_min('2012-04-25') == 12 * 60 + 25      # before Mar 2013: flat before the earliest possible release
    assert h.exit_min('2020-03-03') == 9 * 60 + 55       # the 10am emergency cut
    assert h.exit_min('2016-12-14') == 13 * 60 + 55

def test_live_fomc_calendar_covers_the_race():
    from calendar_us import FOMC
    assert sum(1 for d in FOMC if d.startswith('2027')) >= 8, 'the live FOMC calendar must cover 2027'

# ---------------------------------------------------------------- data integrity (fast)
def _manifest_ok(folder, n):
    man = json.load(open(os.path.join(ROOT, 'data', folder, 'MANIFEST.json')))
    files = man['files']; assert len(files) == n
    for name, info in files.items():
        p = os.path.join(ROOT, 'data', folder, name)
        assert os.path.exists(p), name
        assert hashlib.sha256(open(p, 'rb').read()).hexdigest() == info['sha256'], f'{name} changed since it was verified'

def test_lockbox_2010_2020_untouched(): _manifest_ok('lockbox2010', 22)
def test_gold_data_untouched(): _manifest_ok('extra', 4)

def test_live_engine_never_reads_the_lockbox():
    """The live engine must never touch the sealed 2010-2020 data. Only the downloader may name the data folder.
    (Reading a RESULTS file such as cards_lockbox2010.json is fine; research scripts open the lockbox deliberately.)"""
    for f in glob.glob(os.path.join(ROOT, 'engine', '*.py')):
        if os.path.basename(f) == 'fetch_lockbox.py': continue
        assert not re.search(r'(?<![_A-Za-z])lockbox2010', open(f).read()), f'{f} refers to the lockbox data'

def test_preregistered_lists_intact():
    import adjustments, adjustments2
    assert len(adjustments.A) == 109 and len(adjustments2.A) == 17

def test_site_template_has_data_slot():
    assert '/*__DATA__*/null' in open(os.path.join(ROOT, 'engine', 'site_template.html')).read()

# ---------------------------------------------------------------- loaders (slow: needs the 1-minute data)
@pytest.fixture(scope='session')
def c():
    import common
    return common

def test_contract_rolls_found(c):
    assert len(c.roll('NQ')) == 23 and len(c.roll('ES')) == 23     # the roll-day bug: this used to be 0

def test_no_duplicate_minutes(c):
    D, _ = c.nb_load('NQ')                                          # the Sep-2026 overlap bug: this used to be > 0
    assert sum(len(v) - len({x[0] for x in v}) for v in D.values()) == 0

def test_no_thin_sessions(c):
    assert len(c.bad_days('NQ')) == 0

# ---------------------------------------------------------------- pinned strategy results (slow)
PINS = dict(quantlab=(1302, 191.49), noiseband=(859, 52.0), atrband=(819, 50.9), expiry=(130, 23.06))
@pytest.mark.parametrize('name', list(PINS))
def test_strategy_results_pinned(c, name):
    t = dict(quantlab=lambda: c.walkforward(c.quantlab('NQ', skip_fomc=True)), noiseband=lambda: c.walkforward(c.noiseband('NQ')),
             atrband=lambda: c.atrband('NQ'), expiry=lambda: c.opex('NQ') + c.opex('ES'))[name]()
    t = [x for x in t if x['month'] <= WINDOW]
    n, R = PINS[name]
    assert len(t) == n, f'{name}: {len(t)} trades, pinned {n}'
    assert abs(sum(x['gross'] - x['cost'] for x in t) - R) < 0.05, f'{name}: result changed from {R}R'

# ---------------------------------------------------------------- live paper book (Task 1, Amendment 6)
def _live():
    import live
    return live

def test_live_fetches_all_four_markets():
    """Rolls come from the days all four markets share, so the nightly top-up must fetch all four (council point 3)."""
    import fetch_databento as fd
    assert set(fd.MARKETS) == set(_live().MARKETS) == {'NQ', 'ES', 'YM', 'RTY'}

def test_live_sizing_rounds_down():
    lv = _live()
    assert lv.contracts(dict(sym='NQ', risk_pts=89.75), 98783.86, 1.0) == 5          # $987.84 / $179.50 = 5.5 -> 5
    assert lv.contracts(dict(sym='NQ', risk_pts=600.0), 100000, 1.0) == 0           # $1,200 a micro: too wide, skipped
    assert lv.contracts(dict(sym='ES', risk_pts=19.9), 100000, 1.0) == 10           # $5/pt
    assert lv.contracts(dict(sym='NQ', risk_pts=0.5), 100000, 1.0) == lv.MAX_CONTRACTS

def test_live_chain_detects_edits():
    lv = _live(); prev = '0' * 64; L = []
    for i, d in enumerate(('2027-01-04', '2027-01-05')):
        e = dict(seq=i, date=d, status='booked', equity_start=1.0, equity_end=1.0, trades=[], skipped=[], prev_hash=prev); e['hash'] = lv.ehash(e); prev = e['hash']; L.append(e)
    assert lv.verify_chain(L) is None
    L[0]['equity_end'] = 2.0; assert 'edited' in lv.verify_chain(L)
    L[0]['hash'] = lv.ehash(L[0]); assert 'link' in lv.verify_chain(L)               # re-hashing one entry breaks the next link

def test_live_band_preregistered():
    p = os.path.join(ROOT, 'research', 'results', 'live_band.json')
    assert hashlib.sha256(open(p, 'rb').read()).hexdigest() == '9f5992a96a67a4e7aa6e3a2deef81697af455f8148b16e6169b09a71102c03e4', 'the band is pre-registered (Amendment 6)'

def test_live_practice_october(c, tmp_path):
    """A full practice book over October 2026 on real data: books 22 days, re-running books nothing and passes the replay check,
    and editing the ledger halts the book."""
    import datetime as dt, json as js
    from zoneinfo import ZoneInfo
    lv = _live(); old = lv.BOOKS['practice']['start']; lv.BOOKS['practice']['start'] = '2026-10-01'
    try:
        now = dt.datetime(2026, 10, 31, 12, 0, tzinfo=ZoneInfo('America/New_York'))
        assert lv.run('practice', now=now, root=str(tmp_path)) == 0
        f = tmp_path / 'data' / 'ledger_practice'; st = js.load(open(f / 'status.json'))
        assert st['days'] == 22 and st['trades'] == 54 and abs(st['equity'] - 102235.64) < 0.01, st
        assert 'flat' in st['checks']['positions']
        assert lv.run('practice', now=now, root=str(tmp_path)) == 0
        st = js.load(open(f / 'status.json')); assert st['booked_now'] == [] and st['checks']['replay'].startswith('ok (22')
        lines = open(f / 'ledger.jsonl').read().splitlines(); e = js.loads(lines[3]); e['equity_end'] += 1; lines[3] = js.dumps(e, sort_keys=True)
        open(f / 'ledger.jsonl', 'w').write('\n'.join(lines) + '\n')
        assert lv.run('practice', now=now, root=str(tmp_path)) == 2
        assert js.load(open(f / 'status.json'))['state'] == 'halted: chain broken'
    finally: lv.BOOKS['practice']['start'] = old


def test_public_charts_use_yahoo_not_databento(monkeypatch):
    """The public chart files must be built from Yahoo (engine/public_bars.py): Databento's licence forbids republishing."""
    import datetime as dt, json as js, public_bars as pb
    t0 = int(dt.datetime(2026, 11, 5, 9, 30, tzinfo=pb.NY).timestamp())
    monkeypatch.setattr(pb, '_get', lambda sym, q: [(t0 + 300 * i, 100.0 + i, 101.0 + i, 99.0 + i, 100.5 + i) for i in range(78)])
    s = pb.sessions('NQ')
    assert list(s) == ['2026-11-05'] and len(s['2026-11-05']) == 78 and s['2026-11-05'][0] == [570, 100.0, 101.0, 99.0, 100.5]
    monkeypatch.setattr(pb, '_get', lambda sym, q: (_ for _ in ()).throw(OSError('down')))
    assert pb.sessions('NQ') == {} and pb.daily('NQ') == []          # Yahoo down: nothing, and never a Databento fallback
    c = js.load(open(os.path.join(ROOT, 'docs', 'data', 'chart.json')))
    assert c.get('source') == pb.SOURCE
    for f in ('portfolio.py', 'live.py'):
        src = open(os.path.join(ROOT, 'engine', f)).read()
        body = src[src.index('def chart_data(' if f == 'portfolio.py' else 'def bars5('):src.index("if __name__ == '__main__':")]
        assert 'public_bars' in body and 'c.prep(' not in body and 'c.daily(' not in body
