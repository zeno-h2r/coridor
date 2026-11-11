import re,glob,os,json,collections
paths=collections.Counter()
for f in glob.glob('state/js/*.js'):
    d=open(f,encoding='utf-8',errors='replace').read()
    for m in re.finditer(r'[`"\'](/?api/v[12]/[A-Za-z0-9_\-/{}$:.%]+)', d):
        p=m.group(1)
        p=re.sub(r'\$\{[^}]*\}','{id}',p)
        p=p.lstrip('/')
        paths[p]+=1
out=sorted(paths.items(), key=lambda x:-x[1])
json.dump(dict(out), open('state/surface_47.json','w'), indent=1)
print("unique api paths:", len(out))
for p,c in out[:80]: print(c,p)
