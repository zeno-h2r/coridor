import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
TOK={r:open(f'/tmp/bac_{r}').read().strip() for r in ['OWNER','SYSADMIN','TESTER','TPU']}
tag='ZXP'+uuid.uuid4().hex[:5]
node=lambda d: [{"id":"1","description":d,"nextStep":[],"connectorLabel":[],
                 "shapeType":"Process","function":"","phase":"","altText":""}]
print("=== POST /documents/flowchart by role (benign node) ===")
for r in ['OWNER','SYSADMIN','TESTER','TPU']:
    c,b=req('POST','/api/v1/documents/flowchart',node(f"ZX{tag}"),tok=TOK[r])
    url=''
    try: url=json.loads(b).get('url','')[:70]
    except: pass
    print(f"  {r:9} -> {c}  {url or b[:90].replace(chr(10),' ')}")
print()
print("=== control: TPU direct access to narratives/documents ===")
for p in ['/api/v1/narratives/38','/api/v1/document_versions/1371','/api/v1/documents/330']:
    c,b=req('GET',p,tok=TOK['TPU'])
    print(f"  TPU {c} {p:36} {b[:80].replace(chr(10),' ')}")
