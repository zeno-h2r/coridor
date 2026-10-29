#!/usr/bin/env python3
"""Devalue payload -> published entry fields; diff vs preview. v2 shallow resolve."""
import json, os, hashlib

DD = '/home/z/my-project/recon/draftdiff'

def resolve_shallow(arr, idx, depth=0, maxdepth=8):
    if depth > maxdepth: return None
    v = arr[idx]
    if isinstance(v, dict):
        out = {}
        for k, r in v.items():
            if isinstance(r, int) and 0 <= r < len(arr):
                out[k] = resolve_shallow(arr, r, depth+1, maxdepth)
            else:
                out[k] = r
        return out
    if isinstance(v, list):
        out = []
        for r in v:
            if isinstance(r, int) and 0 <= r < len(arr):
                out.append(resolve_shallow(arr, r, depth+1, maxdepth))
            else:
                out.append(r)
        return out
    return v

def collect_entries(arr):
    ents = {}
    for i, v in enumerate(arr):
        if not isinstance(v, dict): continue
        meta_ref, sys_ref, f_ref = v.get('metadata'), v.get('sys'), v.get('fields')
        if not all(isinstance(x, int) for x in (sys_ref, f_ref)): continue
        try:
            sysd = resolve_shallow(arr, sys_ref, maxdepth=4)
        except Exception:
            continue
        if not isinstance(sysd, dict): continue
        eid = sysd.get('id')
        if not isinstance(eid, str) or not (10 <= len(eid) <= 30): continue
        try:
            fields = resolve_shallow(arr, f_ref, maxdepth=8)
        except Exception:
            continue
        if isinstance(fields, dict) and fields:
            ents[eid] = fields
    return ents

def canon(o): return hashlib.sha1(json.dumps(o, sort_keys=True, default=str).encode()).hexdigest()

def norm(fl):
    out = {}
    for k, v in (fl or {}).items():
        if isinstance(v, dict) and set(v.keys()) == {'en-US'}: out[k] = v['en-US']
        else: out[k] = v
    return out

published = {}
for f in sorted(os.listdir(DD + '/payloads')):
    try: raw = json.load(open(DD + '/payloads/' + f))
    except Exception: continue
    if not isinstance(raw, list): continue
    for eid, fl in collect_entries(raw).items():
        published.setdefault(eid, {'fields': fl, 'files': []})['files'].append(f)

print(f"published entries parsed: {len(published)}")

diffs, match, noprev = [], 0, 0
for eid, pub in sorted(published.items()):
    fp = DD + f'/preview/{eid}.json'
    if not os.path.exists(fp): noprev += 1; continue
    try: prev = json.load(open(fp))
    except Exception: noprev += 1; continue
    if not (isinstance(prev, dict) and isinstance(prev.get('fields'), dict)): noprev += 1; continue
    a, b = norm(pub['fields']), norm(prev['fields'])
    if canon(a) == canon(b): match += 1; continue
    ka, kb = set(a), set(b)
    changed = sorted(k for k in ka & kb if canon(a[k]) != canon(b[k]))
    diffs.append({'id': eid, 'files': pub['files'][:4], 'added': sorted(kb - ka),
                  'removed': sorted(ka - kb), 'changed': changed,
                  'prev_revision': prev.get('sys', {}).get('revision')})

print(f"identical: {match} | DIFFERENT: {len(diffs)} | no-preview: {noprev}")
json.dump(diffs, open(DD + '/diffs.json', 'w'), indent=1)
for d in diffs[:30]:
    print(f"  {d['id']} rev={d['prev_revision']} files={d['files'][:2]} +{d['added'][:3]} -{d['removed'][:3]} ~{d['changed'][:5]}")
