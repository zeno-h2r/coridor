import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_OWNER').read().strip()
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+(tok or TOK),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== /documents/{id}/diff — returns htmldiff into setContent ===")
for p in ['/api/v1/documents/1/diff?from=1&to=2',
          '/documents/1/diff?from=1&to=2',
          '/api/v1/documents/1/diff?from=1&to=2&flattened=false']:
    c,b=req('GET',p)
    print(f"\n  {c} {p}")
    print(f"    {b[:300].replace(chr(10),' ')}")
print()
print("=== what document ids exist? ===")
c,b=req('POST','/api/v1/table/query?entities=document_version',
        {"ab:query":{"entities":["document_version"],"filter":{},"include":["document_version"]}})
try:
    inc=json.loads(b).get('included') or []
    print(f"  docver count={len(inc)}")
    docs={}
    for i in inc:
        a=i.get('attributes') or {}
        d=a.get('documentId')
        if d: docs.setdefault(d,[]).append(i['id'])
    for d in list(docs)[:8]:
        print(f"    document {d}: versions {docs[d][:6]}")
except Exception as e: print("  ",c,b[:200])
