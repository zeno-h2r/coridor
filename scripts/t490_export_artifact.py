import json,subprocess,os,time
H=os.environ['H']; BB=os.environ['BB']
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-AuditBoard-Source: SchemaTable Rows']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
TO=open('/tmp/bac_OWNER').read().strip()
print("=== Owner: newest files after the exports (did anything land?) ===")
c,b=req('POST','/api/v1/table/query?entities=file',
        {"ab:query":{"entities":["file"],"filter":{},"include":["file"]}},tok=TO)
try:
    inc=json.loads(b).get('included') or []
    inc=sorted(inc,key=lambda x:int(x['id']),reverse=True)[:8]
    print(f"  total files: {len(json.loads(b).get('included') or [])}")
    for f in inc:
        a=f.get('attributes') or {}
        print(f"    id={f['id']:<5} name={str(a.get('name'))[:44]:46} created={a.get('createdAt')}")
except Exception as e: print("  ",c,b[:200])
print()
print("=== also check attachments (export may attach) ===")
c,b=req('GET','/api/v1/attachments',tok=TO)
try:
    ats=json.loads(b).get('attachments') or []
    ats=sorted(ats,key=lambda x:int(x['id']),reverse=True)[:6]
    for a in ats:
        print(f"    id={a['id']} name={str(a.get('name'))[:40]} type={a.get('type')} created={a.get('created_at')}")
except Exception as e: print("  ",c,b[:150])
