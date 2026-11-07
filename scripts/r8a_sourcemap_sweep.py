#!/usr/bin/env python3
"""Round 8A: sourcemap disclosure sweep across all known JS bundles + static assets.
Checks <chunk>.js.map availability; if found, downloads and inventories sourcesContent."""
import urllib.request, json, sys

W = 'https://www.dutchbros.com/'
chunks = [l.strip() for l in open('/tmp/chunks_to_test.txt') if l.strip()]
# Yext static/client/render assets
extra = [
    '/locations/assets/render/_client.D0QvP5id.js',
    '/locations/assets/client/restaurant.CWOYGQKF.js',
    '/locations/assets/client/city.CE_Bvb6c.js',
    '/locations/assets/client/404.C3qg2MWq.js',
    '/locations/assets/static/index-C2kTBeMo.js',
    '/locations/assets/static/constants-cSgGnIBh.js',
    '/locations/assets/static/Hours-DUsePfCB.js',
]
targets = [c + '.map' for c in chunks] + [e + '.map' for e in extra]

def head(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}, method='GET')
    try:
        r = urllib.request.urlopen(req, timeout=15)
        return r.status, r.headers.get('Content-Type'), len(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('Content-Type'), 0
    except Exception as e:
        return -1, str(e), 0

found = []
for t in targets:
    code, ct, size = head(W + t.lstrip('/'))
    if code == 200 and size > 0:
        found.append((t, size, ct))
        print(f'[+] MAP FOUND {code} {size:>9}b {ct}  {t}')
print(f'\ntested {len(targets)} -> found {len(found)}')
if not found:
    print('sourcemap disclosure: NEGATIVE (all 404/fallback)')
json.dump(found, open('/home/z/my-project/recon/r8_sourcemaps_found.json', 'w'), indent=1)
