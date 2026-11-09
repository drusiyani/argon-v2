"""Build the site (docs/index.html): a research-paper style site with five tabs (Overview, Chart, Research, Brain, Desk), from Argon's data.
The page is a template (engine/site_template.html) plus one embedded DATA object; the heavy tabs load docs/data/*.json on demand.
The old all-in-one dashboard is still built as docs/lab.html (the brain export needs it) but is not linked."""
import os, json, glob, datetime as dt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def J(*p, default=None):
    try: return json.load(open(os.path.join(ROOT, *p)))
    except Exception: return default
P = J('data', 'portfolio.json', default={}) or {}
A = J('research', 'results', 'cards_databento.json', default={}) or {}
B = J('research', 'results', 'cards_lockbox2010.json', default={}) or {}
S1 = J('research', 'results', 'summary.json', default={}) or {}
S2 = J('research', 'results', 'round2', 'summary.json', default={}) or {}
F = J('docs', 'desk_feed.json', default={}) or {}
LG = J('docs', 'data', 'ledger.json', default={}) or {}
LV = J('docs', 'data', 'live_view.json', default={}) or {}
st = LG.get('status') or {}
LEDGER = dict(book=LG.get('book'), state=st.get('state'), equity=st.get('equity'), last=st.get('last_booked'), days=st.get('days', 0),
              checks=st.get('checks', {}), start=st.get('start') or '2026-11-16')
LIVE = dict(date=LV.get('date'), as_of=LV.get('as_of'), n=len(LV.get('trades', [])), open=sum(1 for t in LV.get('trades', []) if t.get('state') == 'open'),
            R=round(sum(t.get('R_now', 0) for t in LV.get('trades', [])), 2))

os.makedirs(os.path.join(ROOT, 'docs', 'data'), exist_ok=True)
notes = []
for f in sorted(glob.glob(os.path.join(ROOT, 'vault', '**', '*.md'), recursive=True)):
    rel = os.path.relpath(f, os.path.join(ROOT, 'vault'))
    if rel.startswith('.'): continue
    notes.append(dict(path=rel, title=os.path.splitext(os.path.basename(f))[0], folder=os.path.dirname(rel) or 'Home', text=open(f, encoding='utf-8', errors='ignore').read()))
json.dump(notes, open(os.path.join(ROOT, 'docs', 'data', 'brain.json'), 'w'), separators=(',', ':'))
RESEARCH = [('Pre-registration', 'PREREGISTRATION.md'), ('Round 1: the 109 adjustments', 'research/ADJUSTMENTS.md'), ('Round 1 results', 'research/results/SUMMARY.md'),
            ('Lockbox 1 (2025-2026)', 'research/results/LOCKBOX.md'), ('Round 2: the 17 adjustments', 'research/ADJUSTMENTS2.md'), ('Round 2 results', 'research/results/round2/SUMMARY.md'),
            ('Lockbox 2 (2011-2020)', 'research/results/LOCKBOX2.md'), ('Variation comparison', 'research/results/VARIATIONS.md'), ('How the research code works', 'research/README.md')]
docs = [dict(title=t, path=p, text=open(os.path.join(ROOT, p), encoding='utf-8').read()) for t, p in RESEARCH if os.path.exists(os.path.join(ROOT, p))]
json.dump(docs, open(os.path.join(ROOT, 'docs', 'data', 'research.json'), 'w'), separators=(',', ':'))

cfg = P.get('config') or {}
DATA = dict(
    risk=cfg.get('risk_pct', 1.0), cost_cap=cfg.get('cost_cap_R', 0.10), live_start='2027-02-01', freeze='2027-01-31T23:59:00Z', killed=P.get('killed', False),
    eras=dict(recent=dict(label='2021–26', note='The backtest. Mostly in-sample: the settings were chosen on it.', book=A.get('book', {}), strategies=A.get('strategies', {})),
              unseen=dict(label='2011–20', note='Sealed until 28 Oct 2026, opened once, used since for comparisons, so no longer an independent test.', book=B.get('book', {}), strategies=B.get('strategies', {}))),
    rounds=dict(r1=S1.get('tested', 109), r1s=len(S1.get('survivors', ['Q24'])), r2=S2.get('tested', 17), r2s=len(S2.get('survivors', []))),
    desk=dict(daytype=F.get('daytype'), score=F.get('daytype_score'), kronos=F.get('kronos'), checked=F.get('checked'), calls=(F.get('score') or {}).get('calls', 0)),
    ledger=LEDGER, live=LIVE,
    built=dt.datetime.now(dt.timezone.utc).strftime('%d %b %Y, %H:%M UTC'))
tpl = open(os.path.join(ROOT, 'engine', 'site_template.html'), encoding='utf-8').read()
page = tpl.replace('/*__DATA__*/null', json.dumps(DATA, separators=(',', ':')).replace('</', '<\\/'))
open(os.path.join(ROOT, 'docs', 'index.html'), 'w', encoding='utf-8').write(page); print('built docs/index.html (site)', len(page))
