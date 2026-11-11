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
print("=== complete the node shape ===")
cands=[
 [{"id":"1","description":f"ZX{tag}","connections":[]}],
 [{"id":"1","description":f"ZX{tag}","edges":[]}],
 [{"id":"1","description":f"ZX{tag}","children":[]}],
 [{"id":"1","description":f"ZX{tag}","next":[]}],
 [{"id":"1","description":f"ZX{tag}","links":[]}],
]
for body in cands:
    c,b=req(body)
    print(f"  {list(body[0].keys())} -> {c} {b[:180].replace(chr(10),' ')}")
    if c=='200':
        print(f"    *** ACCEPTED ***")
        d=json.loads(b)
        print(f"    url={d.get('url','')[:120]}")
        open('/tmp/flow_url','w').write(d.get('url',''))
        break
