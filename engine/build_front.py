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

# ---- the brain as a graph (nodes = notes, links = [[wikilinks]]); the page lays it out itself, so no heavy maths here
import re as _re
_key = {}
for i, n in enumerate(notes):
    for k in (n['title'], os.path.splitext(n['path'])[0]): _key.setdefault(k.lower(), i)
_links = set()
for i, n in enumerate(notes):
    for m in _re.finditer(r'\[\[([^\]|#]+)', n['text']):
        j = _key.get(m.group(1).strip().lower())
        if j is not None and j != i: _links.add((min(i, j), max(i, j)))
_deg = [0] * len(notes)
for a, b in _links: _deg[a] += 1; _deg[b] += 1
json.dump(dict(nodes=[dict(t=n['title'], f=n['folder'].split('/')[0] if n['folder'] != 'Home' else 'Home', d=_deg[i]) for i, n in enumerate(notes)],
               links=sorted(_links), words=sum(len(n['text'].split()) for n in notes)),
          open(os.path.join(ROOT, 'docs', 'data', 'graph.json'), 'w'), separators=(',', ':'))

# ---- live calendar: every booked ledger day, with its trades and that morning's calls (the decisions)
_calls = {}
try:
    for line in open(os.path.join(ROOT, 'data', 'daytype.jsonl')):
        if line.strip():
            c = json.loads(line); _calls[c['date']] = c
except Exception: pass
def _call(c):
    if not c: return None
    mem = {k: (dict(p=v.get('trend_probability'), s=v.get('size'), why=(v.get('reason') or '')[:240]) if v else None) for k, v in ((c.get('council') or {}).get('members') or {}).items()}
    ai = c.get('ai') or {}
    return dict(at=c.get('made_at'), ai=dict(p=ai.get('trend_probability'), s=ai.get('size'), why=(ai.get('reason') or '')[:240]), used=c.get('ai_size_used'),
                rule=c.get('dumb_size'), rnd=c.get('random_size'), mkt=(c.get('market') or {}).get('size'), seats=mem,
                errors=sorted((c.get('errors') or {}).keys()), heads=((c.get('inputs') or {}).get('headlines') or [])[:6])
_live, _eq = {}, dict(LG.get('equity') or [])
for d in sorted(LG.get('days') or [], key=lambda x: x['date']):
    e1 = _eq.get(d['date']); e0 = (e1 - d.get('usd', 0)) if e1 else None
    _live[d['date']] = dict(r=round(100 * d.get('usd', 0) / e0, 3) if e0 else 0, usd=d.get('usd', 0), eq=e1, regime=(d.get('regime') or {}).get('label'),
                            t=[[t.get('strategy'), 1 if t.get('side') == 'long' else -1, t.get('entry_time'), t.get('exit_time'), round(t.get('R', 0), 2), 1, t.get('market'), round(t.get('usd', 0), 2)] for t in d.get('trades', [])],
                            skipped=d.get('skipped') or [], call=_call(_calls.get(d['date'])), note=f"Live/Days/{d['date']}")
json.dump(dict(book=LG.get('book'), days=_live), open(os.path.join(ROOT, 'docs', 'data', 'live_days.json'), 'w'), separators=(',', ':'))
RESEARCH = [('Pre-registration', 'PREREGISTRATION.md'), ('Round 1: the 109 adjustments', 'research/ADJUSTMENTS.md'), ('Round 1 results', 'research/results/SUMMARY.md'),
            ('Lockbox 1 (2025-2026)', 'research/results/LOCKBOX.md'), ('Round 2: the 17 adjustments', 'research/ADJUSTMENTS2.md'), ('Round 2 results', 'research/results/round2/SUMMARY.md'),
            ('Lockbox 2 (2011-2020)', 'research/results/LOCKBOX2.md'), ('Variation comparison', 'research/results/VARIATIONS.md'), ('How the research code works', 'research/README.md')]
docs = [dict(title=t, path=p, text=open(os.path.join(ROOT, p), encoding='utf-8').read()) for t, p in RESEARCH if os.path.exists(os.path.join(ROOT, p))]
for f in sorted(glob.glob(os.path.join(ROOT, 'analysis', 'BATCH*_RESULTS.md')), key=lambda x: -int(''.join(c for c in os.path.basename(x) if c.isdigit()) or 0)):
    t = open(f, encoding='utf-8').read(); h = next((l.lstrip('# ').strip() for l in t.splitlines() if l.startswith('#')), os.path.basename(f))
    docs.append(dict(title=h, path=os.path.relpath(f, ROOT), text=t, kind='batch'))
for d in docs: d.setdefault('kind', 'doc')
json.dump(docs, open(os.path.join(ROOT, 'docs', 'data', 'research.json'), 'w'), separators=(',', ':'))

cfg = P.get('config') or {}
BOOK = J('docs', 'data', 'book.json', default=None)
def _seats():
    """Each seat's record from data/daytype.jsonl: its trend chance on each morning it was asked, and how often it answered."""
    out = {}
    try: rows = [json.loads(x) for x in open(os.path.join(ROOT, 'data', 'daytype.jsonl')) if x.strip()]
    except Exception: return out
    for r in rows:
        for k, m in (((r.get('council') or {}).get('members')) or {}).items():
            s = out.setdefault(k, dict(hist=[], asked=0, answered=0)); s['asked'] += 1
            p = (m or {}).get('trend_probability')
            if p is not None: s['answered'] += 1
            s['hist'].append([r.get('date'), p])
    for s in out.values(): s['hist'] = s['hist'][-20:]
    return {k: v for k, v in out.items() if k in ('claude', 'gpt', 'gemini', 'kimi')}     # retired seats (Llama, DeepSeek) are not shown
DATA = dict(
    risk=cfg.get('risk_pct', 1.0), cost_cap=cfg.get('cost_cap_R', 0.10), live_start='2027-02-01', freeze='2027-01-31T23:59:00Z', killed=P.get('killed', False),
    eras=dict(recent=dict(label='2021–26', note='The backtest. Mostly in-sample: the settings were chosen on it.', book=A.get('book', {}), strategies=A.get('strategies', {})),
              unseen=dict(label='2011–20', note='Sealed until 28 Oct 2026, opened once, used since for comparisons, so no longer an independent test.', book=B.get('book', {}), strategies=B.get('strategies', {}))),
    rounds=dict(r1=S1.get('tested', 109), r1s=len(S1.get('survivors', ['Q24'])), r2=S2.get('tested', 17), r2s=len(S2.get('survivors', []))),
    desk=dict(daytype=F.get('daytype'), score=F.get('daytype_score'), kronos=F.get('kronos'), checked=F.get('checked'), calls=(F.get('score') or {}).get('calls', 0)),
    ledger=LEDGER, live=LIVE,
    book=BOOK, strategies=J('research', 'results', 'strategies.json', default=None),
    history=[dict(date=h.get('date'), at=h.get('made_at'), p=(h.get('ai') or {}).get('trend_probability'), s=h.get('ai_size_used'), rule=h.get('dumb_size')) for h in (F.get('daytype_history') or [])][-15:],
    equity=LG.get('equity') or [],
    seats=_seats(),
    built=dt.datetime.now(dt.timezone.utc).strftime('%d %b %Y, %H:%M UTC'))
tpl = open(os.path.join(ROOT, 'engine', 'site_template.html'), encoding='utf-8').read()
page = tpl.replace('/*__DATA__*/null', json.dumps(DATA, separators=(',', ':')).replace('</', '<\\/'))
open(os.path.join(ROOT, 'docs', 'index.html'), 'w', encoding='utf-8').write(page); print('built docs/index.html (site)', len(page))
