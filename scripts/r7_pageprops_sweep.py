#!/usr/bin/env python3
"""Round 7: multi-sample pageProps JSON sweep across store detail pages.
Extract JSON.parse(decodeURIComponent("...")) payloads, diff field sets,
harvest endpoint/URL/key-like strings. Read-only analysis of in-scope pages."""
import re, json, os, sys, urllib.parse, collections

DIR = '/home/z/my-project/recon/storesweep'
OUT = '/home/z/my-project/recon/storesweep'

pages = {}
for fn in sorted(os.listdir(DIR)):
    if not fn.startswith('p_') or not fn.endswith('.html'):
        continue
    raw = open(os.path.join(DIR, fn), encoding='utf-8', errors='replace').read()
    if len(raw) < 200000:   # skip city-level pages
        continue
    # pageProps: JSON.parse(decodeURIComponent("..."))
    m = re.search(r'pageProps:\s*JSON\.parse\(decodeURIComponent\("((?:[^"\\]|\\.)*)"\)\)', raw)
    if not m:
        print(f'[!] {fn}: pageProps pattern NOT found'); continue
    try:
        data = json.loads(urllib.parse.unquote(json.loads('"' + m.group(1) + '"')))
    except Exception as e:
        print(f'[!] {fn}: parse fail {e}'); continue
    pages[fn] = data
    print(f'[+] {fn}: parsed, top keys={list(data.keys())}')

if not pages:
    sys.exit('nothing parsed')

# ---- 1. diff top-level field sets ----
sets = {fn: set(d.keys()) for fn, d in pages.items()}
allk = set().union(*sets.values())
print('\n== top-level key union ==')
for k in sorted(allk):
    present = [fn for fn, s in sets.items() if k in s]
    print(f'{"ALL" if len(present)==len(sets) else str(len(present))+"/"+str(len(sets))}  {k}')

# ---- 2. recursive field-path census (3 levels) ----
def paths(o, base='', depth=0):
    out = set()
    if depth > 6: return out
    if isinstance(o, dict):
        for k, v in o.items():
            p = f'{base}.{k}' if base else k
            out.add(p); out |= paths(v, p, depth+1)
    elif isinstance(o, list):
        for v in o[:2]:
            out |= paths(v, base + '[]', depth+1)
    return out
pp = {fn: paths(d) for fn, d in pages.items()}
union = set().union(*pp.values())
common = set.intersection(*pp.values())
only = union - common
print(f'\n== path union {len(union)}, common {len(common)}, NOT-common {len(only)} ==')
for p in sorted(only):
    owners = [fn.split('_')[1] for fn, s in pp.items() if p in s]
    print(f'  {p}  <-{",".join(owners)}')

# ---- 3. endpoint / url / key-like string harvest ----
blob = json.dumps(pages)
urls = sorted(set(re.findall(r'https?://[^\s"\')<>\\]+', blob)))
print('\n== URLs in pageProps ==')
for u in urls: print(' ', u[:150])

pat_int = sorted(set(re.findall(r'/api/[a-zA-Z0-9_\-/\.]+', blob)))
print('\n== /api/ refs ==')
for p in pat_int: print(' ', p)

# key-like tokens
keys = sorted(set(re.findall(r'"([a-zA-Z0-9_]{16,40})"', blob)))
sus = [k for k in keys if re.search(r'(key|token|secret|auth|id$|Id$|api)', k, re.I)]
print('\n== key/token-like field names (deduped values) ==')
print(' ', ', '.join(sus[:60]))

# ---- 4. save full props for diff + next steps ----
with open(os.path.join(OUT, 'pageprops_all.json'), 'w') as f:
    json.dump({fn: pages[fn] for fn in pages}, f, indent=1)
print(f'\nsaved -> {OUT}/pageprops_all.json ({sum(len(json.dumps(v)) for v in pages.values())} bytes total)')
