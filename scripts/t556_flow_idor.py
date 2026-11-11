import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TP=open('/tmp/bac_TPU').read().strip()
TO=open('/tmp/bac_OWNER').read().strip()
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== does flowchart accept a narrativeId / existing doc reference? ===")
for extra in [{"narrativeId":38},{"narrative_id":38},{"documentId":330},{"document_id":330}]:
    node=[{"id":"1","description":"ZX","nextStep":[],"connectorLabel":[],
           "shapeType":"Process","function":"","phase":"","altText":"", **extra}]
    c,b=req('POST','/api/v1/documents/flowchart',node,tok=TP)
    print(f"  node+{list(extra)[0]:14} -> {c} {b[:110].replace(chr(10),' ')}")
print()
print("=== body-level extra keys ===")
for body in [{"nodes":[{"id":"1","description":"ZX","nextStep":[],"connectorLabel":[],"shapeType":"Process","function":"","phase":"","altText":""}],"narrativeId":38}]:
    c,b=req('POST','/api/v1/documents/flowchart',body,tok=TP)
    print(f"  {c} {b[:150].replace(chr(10),' ')}")
print()
print("=== does the response leak narrative content when given an id? ===")
c,b=req('POST','/api/v1/documents/flowchart',
        [{"id":"38","description":"ZX","nextStep":[],"connectorLabel":[],
          "shapeType":"Process","function":"","phase":"","altText":""}],tok=TP)
print(f"  id=38 -> {c} {b[:200].replace(chr(10),' ')}")
