"""Nightly lab, step 1: Gemini proposes one strategy idea (or none) as a GitHub issue. Reads the lab files and the
open issues, sends them to Gemini through OpenRouter, opens the issue. Never touches data or the live book."""
import json, os, sys, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.environ.get('GITHUB_REPOSITORY', 'drusiyani/argon-v2'); GH = os.environ.get('GITHUB_TOKEN', '')
MODEL = os.environ.get('LAB_GEMINI_MODEL', 'google/gemini-4-argon')

def http(url, body=None, headers=None, method=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Content-Type': 'application/json', **(headers or {})}, method=method)
    with urllib.request.urlopen(req, timeout=300) as r: return json.loads(r.read())

def gh(path, body=None):
    return http('https://api.github.com/repos/' + REPO + path, body,
                {'Authorization': 'Bearer ' + GH, 'Accept': 'application/vnd.github+json'}, 'POST' if body else 'GET')

def read(p):
    try: return open(os.path.join(ROOT, p)).read()
    except OSError: return '(missing)'

PROMPT = """You are a sceptical senior quant researcher for Argon, a pre-registered paper-trading research project on Nasdaq
futures. Think slowly and carefully. Below are the lab rules, the full list of what has already been tested, the log, and
your earlier ideas (GitHub issues).

STEP 1 - Come up with 5 candidate ideas privately, then kill the weak ones. Throw out any idea that:
- repeats or is a close variant of anything in TRIED.md, the log, or an earlier issue
- needs data we don't have (no volume, order book or options data before 2021; only 1-minute NQ/ES prices, daily VIX/VXN,
  T-bills, macro/FOMC calendar)
- trades often for a small edge (cost is about 1 NQ point per round trip; it must clear that by a wide margin)
- is basically another long-Nasdaq bet (it stacks on the core and fails)
- has no clear reason to work: say WHO is on the other side and WHY they keep losing (forced flows, hedging, rebalancing,
  behaviour), ideally backed by a real paper you name (only cite papers you are sure exist)
- needs more than 2 free parameters

STEP 2 - If none survive, reply with a first line exactly "TITLE: none tonight" and then say why in under 120 words.
A rubbish idea is worse than no idea.

STEP 3 - If one survives, reply with a first line "TITLE: <short idea name>" and then, under 400 words, no hype:
1. The idea in one sentence
2. Why it should work (mechanism + paper)
3. Exact rules: entry time/condition, exit, stop, size, market
4. Why it is NOT in TRIED.md (name the closest past test and the difference)
5. Expected trades per year and rough edge per trade vs cost
6. How it fits the book (does it make money when the core loses?)
7. Pass bar: discover on 2011-2020 only, confirm once on 2021-2026, must raise the book's Sharpe in both eras
8. The strongest argument AGAINST it, and your honest chance it passes (most ideas fail)
"""

def main():
    issues = gh('/issues?state=all&per_page=50')
    past = '\n\n'.join('#%d %s\n%s' % (i['number'], i['title'], (i.get('body') or '')[:1500])
                       for i in issues if i['title'].startswith('Gemini idea') and 'pull_request' not in i)
    ctx = ('\n\n=== lab/README.md ===\n' + read('lab/README.md') + '\n\n=== lab/TRIED.md ===\n' + read('lab/TRIED.md') +
           '\n\n=== lab/LOG.md ===\n' + read('lab/LOG.md') + '\n\n=== Earlier Gemini ideas (issues) ===\n' + (past or '(none yet)'))
    body = {'model': MODEL, 'max_tokens': 16000, 'reasoning': {'effort': 'high'},
            'messages': [{'role': 'user', 'content': PROMPT + ctx}]}
    r = http('https://openrouter.ai/api/v1/chat/completions', body, {'Authorization': 'Bearer ' + os.environ['OPENROUTER_API_KEY']}, 'POST')
    text = (r['choices'][0]['message'].get('content') or '').strip()
    if not text: sys.exit('empty reply from Gemini')
    first, _, rest = text.partition('\n')
    name = first.replace('TITLE:', '').strip() if first.upper().startswith('TITLE:') else 'untitled'
    usd = (r.get('usage') or {}).get('cost')
    note = '\n\n---\n_Model: %s. Cost: %s. Not tested yet: Claude pre-registers and runs it._' % (MODEL, ('$%.3f' % usd) if usd else 'n/a')
    i = gh('/issues', {'title': 'Gemini idea: ' + name, 'body': (rest.strip() or text) + note, 'labels': ['lab']})
    print(i['html_url'])
    with open(os.environ.get('GITHUB_OUTPUT', '/dev/null'), 'a') as f: f.write('url=%s\ntitle=%s\n' % (i['html_url'], name))

if __name__ == '__main__': main()
