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
print("=== Tester: narrative 31 -> document id, then diff ===")
c,b=req('GET','/api/v1/narratives/31')
try:
    o=json.loads(b)['narratives'][0]
    dv=o.get('alias_latest_document_version_id')
    print(f"  narrative 31 docver={dv}")
except Exception as e: print("  ",c,b[:150]); dv=None
if dv:
    c,b=req('GET',f'/api/v1/document_versions/{dv}')
    try:
        d=json.loads(b)['document_versions'][0]
        print(f"  docver {dv}: document_id={d.get('document_id')} body={str(d.get('body'))[:60]!r}")
        docid=d.get('document_id')
    except: docid=None
    if docid:
        for q in [f'/api/v1/documents/{docid}/diff?from={dv}&to={dv}',
                  f'/api/v1/documents/{docid}/diff?from=1&to={dv}']:
            c,b=req('GET',q)
            print(f"\n  {c} {q}")
            print(f"    {b[:250].replace(chr(10),' ')}")
