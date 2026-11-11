import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TT=open('/tmp/bac_TESTER').read().strip()
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+(tok or TT),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== document 330 full body (existing payload) ===")
c,b=req('GET','/api/v1/document_versions/1371')
d=json.loads(b)['document_versions'][0]
print(f"  body = {d.get('body')!r}")
print(f"  flat = {str(d.get('flat_body'))[:200]!r}")
print(f"  user_id={d.get('user_id')} is_published={d.get('is_published')}")
print()
print("=== which narrative owns document 330? ===")
c,b=req('GET','/api/v1/narratives/31')
o=json.loads(b)['narratives'][0]
print(f"  narrative 31 name={o.get('name')!r} docver={o.get('alias_latest_document_version_id')}")
