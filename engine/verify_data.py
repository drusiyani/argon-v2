"""Check local raw data files against the public manifests (data/*/MANIFEST.json).

The raw files are private (Databento's licence; HistData publishes no licence), so the repo publishes only their names,
sizes and SHA-256 hashes. Put your own copies in data/<folder>/ and run this to see whether they are byte-for-byte the
files Argon used. Usage: python engine/verify_data.py [folder ...]   Exit code 1 if any file present doesn't match."""
import os, sys, json, glob, hashlib
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def check(folder):
    mp = os.path.join(ROOT, 'data', folder, 'MANIFEST.json')
    if not os.path.exists(mp): return None
    files = json.load(open(mp)).get('files', {}); ok = bad = missing = 0
    for name, info in sorted(files.items()):
        p = os.path.join(ROOT, 'data', folder, name)
        if not os.path.exists(p): missing += 1; continue
        if hashlib.sha256(open(p, 'rb').read()).hexdigest() == info['sha256']: ok += 1
        else: bad += 1; print(f'  MISMATCH {folder}/{name}')
    print(f'{folder}: {ok} match, {bad} differ, {missing} not present (of {len(files)})')
    return bad

if __name__ == '__main__':
    folders = sys.argv[1:] or sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(ROOT, 'data', '*', 'MANIFEST.json')))
    res = [check(f) for f in folders]
    sys.exit(1 if any(r for r in res) else 0)
