#!/usr/bin/env python3
"""Round 7b: unkeyed header reflection / cache-poisoning surface audit on www.
Bounded, read-only GET probes with distinct marker values."""
import urllib.request, re, sys

BASE = 'https://www.dutchbros.com'
MARK = 'zeno0h7x.probe.example'

# (label, url, headers)
probes = [
    ('xfh-menu',      '/menu/',            {'X-Forwarded-Host': MARK}),
    ('xfh-home',      '/',                 {'X-Forwarded-Host': MARK}),
    ('xfp-home',      '/',                 {'X-Forwarded-Proto': 'https'}),
    ('xoh-home',      '/',                 {'X-Original-URL': '/' + MARK}),
    ('xrw-home',      '/',                 {'X-Rewrite-URL': '/' + MARK}),
    ('xfh-loc',       '/locations/',       {'X-Forwarded-Host': MARK}),
    ('xfh-store',     '/locations/tx/mesquite/105-commerce-way', {'X-Forwarded-Host': MARK}),
    ('xff-home',      '/',                 {'X-Forwarded-For': '203.0.113.7'}),
    ('host-sni',      '/',                 {'Host': MARK}),   # will likely be rejected by CF SNI
]
cache_headers = ['cache-control', 'cf-cache-status', 'age', 'x-cache', 'etag', 'last-modified', 'set-cookie', 'vary']

for label, path, extra in probes:
    req = urllib.request.Request(BASE + path, headers={'User-Agent': 'Mozilla/5.0 (research)', **extra})
    try:
        r = urllib.request.urlopen(req, timeout=20)
        body = r.read().decode('utf-8', 'replace')
        code = r.status; hd = dict(r.headers)
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', 'replace'); code = e.code; hd = dict(e.headers)
    except Exception as e:
        print(f'[{label}] ERROR {e}'); continue
    refl_body = MARK in body
    refl_h = {k: v for k, v in hd.items() if MARK in v}
    ch = {k: hd.get(k) for k in cache_headers if hd.get(k)}
    print(f'[{label}] {code} body_refl={refl_body} hdr_refl={refl_h or "-"}')
    print(f'    cache: {ch}')

# what URL shapes appear in body when XFH set?
req = urllib.request.Request(BASE + '/menu/', headers={'User-Agent': 'Mozilla/5.0 (research)', 'X-Forwarded-Host': MARK})
r = urllib.request.urlopen(req, timeout=20)
body = r.read().decode('utf-8', 'replace')
ctxs = [m.group(0)[:160].replace('\n', ' ') for m in re.finditer(r'.{80}(dutchbros\.com|example)[^"\x27<]{0,60}', body)][:8]
print('\n[XFH menu] URL-ish contexts (first 8):')
for c in ctxs: print('  ', c)
