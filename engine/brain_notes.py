"""Argon's Brain (Obsidian vault): one note per booked trading day, one page per month, plus the Decisions page (Amendment 8).

Each day note has every trade, every AI's morning call (solo, council round 1, council round 2), the rule and random sizers,
the headlines the AIs saw, and a plain-English analysis. The ledger stays the official record: these notes are summaries,
not hash-chained, and the AIs NEVER read them (their memory is only their own scorecard).
Usage: python engine/brain_notes.py [official|practice]"""
import os, sys, json, collections, datetime as dt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS = dict(official='data/ledger', practice='data/ledger_practice')
VAULT = os.path.join(ROOT, 'vault', 'Live')
def J(*p, default=None):
    try: return json.load(open(os.path.join(ROOT, *p)))
    except Exception: return default
def read(p): return [json.loads(x) for x in open(p) if x.strip()] if os.path.exists(p) else []
def calls():
    out = {}
    for r in read(os.path.join(ROOT, 'data', 'daytype.jsonl')): out[r['date']] = r
    return out
def sz(x): return '?' if x is None else ('veto' if x == 0 else f'{x:g}x')
def call_line(name, v):
    if not v: return f'| {name} | no answer | | |'
    return f"| {name} | {v.get('trend_probability', 0):.0f}% | {sz(v.get('size'))} | {(v.get('reason') or '').replace('|', '/')[:160]} |"
def day_note(name, e, c, reg, summary, label):
    d = e['date']; usd = e['equity_end'] - e['equity_start']; T = e['trades']
    L = [f"# {d} · {name} book", '', f"#argon/day · [[Live/Months/{d[:7]}|{d[:7]}]] · [[Live/Decisions|Decisions]]", '',
         f"- **Result:** {len(T)} trade{'s' * (len(T) != 1)}, {usd:+,.2f} dollars; account ${e['equity_end']:,.2f}",
         f"- **Market:** {(reg or {}).get('label', 'unknown')}" + (f" (range {reg['range_ratio']}x its 20-day average)" if reg else '') +
         (f"; it was a **{'TREND' if label else 'CHOP'}** day by the 60% rule" if label is not None else ''),
         f"- **Ledger:** hash `{e['hash'][:16]}`, code `{e['code_commit']}`"]
    if summary: L += ['', '> ' + summary]
    L += ['', '## Trades', '']
    if T:
        L += ['| strategy | side | micros | entry → exit | stop | R | $ |', '|---|---|---|---|---|---|---|']
        L += [f"| {t['strategy']} | {t['side']} | {t['contracts']} {t['contract']} | {t['entry']:.2f} ({t['entry_time']}) → {t['exit']:.2f} ({t['exit_time']}) | {t['stop']:.2f} | {t['R']:+.2f} | {t['usd']:+,.2f} |" for t in T]
    else: L.append('No trades today.')
    for s in e['skipped']: L.append(f"- Skipped: `{s['id']}` · {s['reason']}")
    if c:
        cn, c2 = c.get('council') or {}, c.get('council_r2') or {}
        L += ['', f"## Morning call ({c.get('made_at')} New York{', late' if c.get('late') else ''})", '', '| who | trend chance | size | reason |', '|---|---|---|---|',
              call_line('Solo AI (Claude)', c.get('ai') if c.get('ai_runs') else None)]
        for k, v in (cn.get('members') or {}).items(): L.append(call_line(f'Council R1 · {k}', v))
        for k, v in (c2.get('members') or {}).items(): L.append(call_line(f'Council R2 · {k}', v))
        L += ['', f"- **Council:** round 1 {sz(cn.get('size')) if cn.get('counted') else 'not counted'} · round 2 {sz(c2.get('size')) if c2.get('counted') else 'not counted'}",
              f"- **One-line rule:** {sz(c.get('dumb_size'))} · **random sizer:** {sz(c.get('random_size'))} · **used today (shadow):** {sz(c.get('ai_size_used'))}"]
        # plain-English analysis
        L += ['', '## Analysis', '']
        if label is not None:
            for who, v in [('The solo AI', c.get('ai') if c.get('ai_runs') else None), ('The council (round 2)', c2 if c2.get('counted') else None)]:
                if v and v.get('trend_probability') is not None:
                    right = (v['trend_probability'] >= 50) == bool(label)
                    L.append(f"- {who} said {v['trend_probability']:.0f}% trend and was **{'right' if right else 'wrong'}**; sizing at {sz(v.get('size'))} "
                             f"{'helped' if (v.get('size', 1) - 1) * sum(t['R'] for t in T) > 0 else ('made no difference' if v.get('size', 1) == 1 or not T else 'hurt')} versus 1x.")
        r1, r2 = cn.get('members') or {}, c2.get('members') or {}
        moved = [k for k in r2 if r2.get(k) and r1.get(k) and r2[k].get('size') != r1[k].get('size')]
        if moved: L.append(f"- After the discussion, {', '.join(moved)} changed their size (watch for herding).")
        if c.get('errors'): L.append(f"- Errors recorded: {', '.join(c['errors'])}.")
        hs = (c.get('inputs') or {}).get('headlines') or []
        if hs: L += ['', '## Headlines the AIs saw', ''] + [f'- {h}' for h in hs]
        if (c.get('inputs') or {}).get('headline_flags'): L += ['', '**Flagged as possible prompt injection (hidden from the AIs):**'] + [f'- {h}' for h in c['inputs']['headline_flags']]
    L += ['', '_Written automatically from the ledger and the morning-call record. The ledger is the official record._']
    return '\n'.join(L) + '\n'
DECISIONS = """# Decisions

#argon/decisions · [[Home]]

Why Argon v2 is built the way it is. Every rule change is also logged as a numbered amendment in `PREREGISTRATION.md`.

| when | decision | why |
|---|---|---|
| Oct 2026 | Four pre-registered intraday rules on NQ and ES futures; the AI sizes trades instead of picking them | a once-a-day call is a fair, testable job for an AI |
| 28 Oct 2026 | Opened the sealed 2011-2020 data once: the book lost money; published it | honesty; that data can no longer be a clean test |
| Nov 2026 | Nightly hash-chained ledger, rebuilt every night (replay check), phone alerts | nobody, including Dru, can quietly change a result |
| Nov 2026 | Freeze moved from 31 Dec to **31 Jan 2027**; Race 1 runs Feb-Dec 2027 | learn from v1's results first; every change before the freeze is logged |
| Nov 2026 | Top generally-available model from each company races, chosen on the freeze date; upgrades only between races | fairness: no AI gets a newer model mid-race |
| Nov 2026 | Solo AI = Claude Opus 5.5; council = Claude, Gemini 4 Argon, GPT-6 Astra, **DeepSeek V4 Pro** (replacing Llama) via OpenRouter | Llama went enterprise-only; DeepSeek is the most different model, which is what the council tests |
| 7 Nov 2026 | Fixed the morning call: Claude 5.5 rejects `temperature` (400 errors); errors are now saved | every call had silently failed |
| Nov 2026 | Same effort level for every AI, no sampling settings | fairness between models |
| Nov 2026 | Sizes 0.5x / 1x / 1.5x / **2x**; one-line rule also reaches 2x; at most **6%** risk in a day | a wider range shows the AI's skill more clearly; the cap stops a bad day sinking the account |
| Nov 2026 | Each AI sees a short **track record** of its own past calls (not the Brain's notes) | lets it calibrate; kept short to save cost; shared commentary would muddy the test |
| Nov 2026 | **Two-round council**: independent private answers, then an anonymous discussion and a final private answer; both scored | tests whether discussion helps or just causes herding |
| Nov 2026 | **Random sizer** as a 'luck' competitor (seed fixed in advance) | if the AIs can't beat random, they have no skill |
| Nov 2026 | Headlines since the previous close from two sources; suspicious ones are hidden and logged | the AIs should read news (their strength) without being hijacked by it |
| Nov 2026 | Prompt caching on the solo AI's three repeat calls | same answers, lower cost |
| Nov 2026 | Every trading day gets a Brain note; this page records the reasons | a readable trail for the write-up and the interview |
| 9 Nov 2026 | Statistics plan fixed in advance and tested on fake data (false alarms 0.5%; ~230 days only detect big edges) | a "no" can't be explained away later, and the low power is admitted up front |
| 9 Nov 2026 | **Market forecaster** competitor (VIX + yesterday's range, frozen) | does the AI know anything the market data doesn't? |
| 9 Nov 2026 | Missed calls are missing, not 1x; each competitor gets its own account | fair comparison on the same days |
| 9 Nov 2026 | Nightly OpenTimestamps stamp of the ledger, Databento vs Yahoo price check, cost alarm | untouchable history, bad data caught early, no surprise bills |
| 9 Nov 2026 | Raw Databento files: licence checked; CME data may not be republished | decision pending (see the to-do) |
"""
def run(name):
    folder = os.path.join(ROOT, BOOKS[name]); L = read(os.path.join(folder, 'ledger.jsonl'))
    reg = J(BOOKS[name], 'regime.json', default={}) or {}; sums = J('docs', 'data', 'daily_summary.json', default={}) or {}
    daily = (J('data', 'portfolio.json', default={}) or {}).get('daily_R', {}); C = calls()
    os.makedirs(os.path.join(VAULT, 'Days'), exist_ok=True); os.makedirs(os.path.join(VAULT, 'Months'), exist_ok=True)
    open(os.path.join(VAULT, 'Decisions.md'), 'w').write(DECISIONS)
    months = collections.defaultdict(list)
    for e in L:
        row = daily.get(e['date']); label = row[3] if row and len(row) > 3 else None
        open(os.path.join(VAULT, 'Days', e['date'] + '.md'), 'w').write(day_note(name, e, C.get(e['date']), reg.get(e['date']), (sums.get(e['date']) or {}).get('text'), label))
        months[e['date'][:7]].append(e)
    for m, es in months.items():
        usd = es[-1]['equity_end'] - es[0]['equity_start']; n = sum(len(e['trades']) for e in es)
        lines = [f'# {m} · {name} book', '', '#argon/month · [[Live/Decisions|Decisions]]', '',
                 f"- {len(es)} sessions, {n} trades, {usd:+,.2f} dollars; account ${es[-1]['equity_end']:,.2f}", '', '| day | trades | $ |', '|---|---|---|']
        lines += [f"| [[Live/Days/{e['date']}|{e['date']}]] | {len(e['trades'])} | {e['equity_end'] - e['equity_start']:+,.2f} |" for e in es]
        open(os.path.join(VAULT, 'Months', m + '.md'), 'w').write('\n'.join(lines) + '\n')
    return len(L)
if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else ('practice' if dt.date.today() < dt.date(2027, 2, 1) else 'official')
    print('brain notes:', run(name), 'days')
