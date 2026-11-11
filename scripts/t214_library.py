import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
c,b=req('GET','/api/v1/library/preload')
print("preload:",c,"len",len(b))
try:
    d=json.loads(b)
    print("  keys:",list(d.keys()))
    inc=d.get('included') or []
    print("  included:",len(inc))
    from collections import Counter
    print("  types:",Counter(i.get('type') for i in inc))
    for i in inc[:6]:
        a=i.get('attributes') or {}
        print(f"   {i.get('type')} id={i.get('id')} keys={sorted(a.keys())[:8]}")
        for k in ['name','email','description','key','value']:
            if k in a: print(f"      {k}={str(a[k])[:90]}")
except Exception as e: print("  err",e,b[:300])
print()
print("=== library/attributes (schema leak?) ===")
c,b=req('GET','/api/v1/library/attributes')
print("  ",c,"len",len(b))
try:
    d=json.loads(b); at=d.get('attributes') or []
    print("  count:",len(at))
    for a in at[:5]: print("   ",json.dumps(a)[:160])
except Exception as e: print("  ",b[:200])
