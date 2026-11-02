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
