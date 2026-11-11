import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TA=open('/tmp/tok_A-231').read().strip()
TB=open('/tmp/tok_B-230').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or TA),'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== B(230) writes secret content into narrative 67 body ===")
NID=open('/tmp/b_narr').read().strip()
c,b=req('PUT',f'/api/v1/narratives/{NID}',{"narrative":{"description":"ZXSECRET-230-ONLY-CONTENT"}},tok=TB)
print(f"  B write description -> {c} {b[:150].replace(chr(10),' ')}")
print()
print("=== A(231) reads narrative 67 - does it see the content? ===")
c,b=req('GET',f'/api/v1/narratives/{NID}',tok=TA)
n=json.loads(b)['narratives'][0]
print(f"  {c} name={n.get('name')!r} description={n.get('description')!r}")
print(f"  alias_latest_document_version_id={n.get('alias_latest_document_version_id')}")
print()
print("=== A(231) reads the DOCUMENT VERSION (actual body) ===")
dv=n.get('alias_latest_document_version_id')
if dv:
    c,b=req('GET',f'/api/v1/document_versions/{dv}',tok=TA)
    print(f"  {c} len={len(b)}")
    try:
        d=json.loads(b)['document_versions'][0]
        print(f"  keys={sorted(d.keys())[:14]}")
        for k in ['body','content','html','text','name']:
            if k in d: print(f"    {k}={str(d[k])[:200]}")
    except Exception as e: print("  ",b[:300])
