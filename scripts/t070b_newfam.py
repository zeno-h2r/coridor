import re,json
new=json.load(open('state/surface_47.json'))
wl=open('worklog.md',encoding='utf-8',errors='replace').read()
def norm(p):
    p=re.sub(r'\{[^}]*\}','',p)
    return p.strip('/').lower()
seen=set()
for m in re.finditer(r'api/v[12]/[A-Za-z0-9_\-/{}.]+', wl):
    seen.add(norm(m.group(0)))
# family = first segment after api/vN
def fam(p):
    parts=p.split('/')
    return '/'.join(parts[:3]) if len(parts)>2 else p
newfams={}
for p in new:
    f=fam(p)
    if norm(p) not in seen:
        newfams.setdefault(f,[]).append(p)
print("families with undocumented paths:", len(newfams))
for f,ps in sorted(newfams.items()):
    print(f"\n## {f}  ({len(ps)})")
    for p in sorted(ps)[:14]: print("   ",p)
