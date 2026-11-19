"""One way to call Claude for every Argon script (19 Nov 2026, Dru's choice: one OpenRouter account for all AIs).

If OPENROUTER_API_KEY is set, Claude is called through OpenRouter; otherwise through Anthropic directly with
ANTHROPIC_API_KEY. Returns (text, usage) where usage includes 'usd' when the route reports it."""
import os, re, json, urllib.request

OR_KEY = os.environ.get('OPENROUTER_API_KEY'); AN_KEY = os.environ.get('ANTHROPIC_API_KEY')
ROUTE = 'openrouter' if OR_KEY else ('anthropic' if AN_KEY else None)

def or_id(model):
    """claude-opus-5-5 -> anthropic/claude-opus-5.5 (OpenRouter's naming). CLAUDE_OR_MODEL overrides it if the id differs."""
    if '/' in model: return model
    return 'anthropic/' + re.sub(r'-(\d+)-(\d+)$', r'-\1.\2', model)

def _post(url, body, headers, timeout):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=dict({'content-type': 'application/json'}, **headers))
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())

def claude(prompt, model, max_tokens=4000, system=None, effort=None, timeout=240):
    if ROUTE == 'openrouter':
        msgs = ([{'role': 'system', 'content': system}] if system else []) + [{'role': 'user', 'content': prompt}]
        body = {'model': os.environ.get('CLAUDE_OR_MODEL') or or_id(model), 'max_tokens': max_tokens, 'messages': msgs, 'usage': {'include': True}}
        if effort: body['reasoning'] = {'effort': effort}
        r = _post('https://openrouter.ai/api/v1/chat/completions', body, {'Authorization': 'Bearer ' + OR_KEY}, timeout)
        u = dict(r.get('usage') or {}); u['usd'] = round(float(u.pop('cost', 0) or 0), 5); u['route'] = 'openrouter'; u['model_reported'] = r.get('model')
        return r['choices'][0]['message']['content'] or '', u
    if ROUTE == 'anthropic':
        body = {'model': model, 'max_tokens': max_tokens, 'messages': [{'role': 'user', 'content': prompt}]}
        if system: body['system'] = system
        if effort: body['output_config'] = {'effort': effort}
        r = _post('https://api.anthropic.com/v1/messages', body, {'x-api-key': AN_KEY, 'anthropic-version': '2023-06-01'}, timeout)
        t = next(b['text'] for b in r['content'] if b.get('type') == 'text'); u = dict(r.get('usage') or {}); u['route'] = 'anthropic'
        return t, u
    raise RuntimeError('no OPENROUTER_API_KEY or ANTHROPIC_API_KEY')
