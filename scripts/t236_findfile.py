import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TB=open('/tmp/tok_B').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','90','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or TB),'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
c,b=req('POST','/api/v1/table/query?entities=file',
        {"ab:query":{"entities":["file"],"filter":{},"include":["file"]}})
print("table/query file:",c,"len",len(b))
try:
    d=json.loads(b); inc=d.get('included') or []
    print("included:",len(inc))
    if inc:
        a=inc[0].get('attributes') or {}
        print("sample keys:",sorted(a.keys()))
        print("sample:",{k:a.get(k) for k in ['name','creatorUserId','uploadUserId','fileableType','fileableId','createdAt']})
        # newest overall
        inc2=sorted(inc,key=lambda x:int(x['id']),reverse=True)[:5]
        for f in inc2:
            at=f.get('attributes') or {}
            print(f"   id={f['id']} name={at.get('name')} creator={at.get('creatorUserId')}")
except Exception as e: print("err",e,b[:300])
