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
print("=== full node shape ===")
for body in [
 [{"id":"1","description":f"ZX{tag}","nextStep":[],"connectorLabel":[],"type":"Process"}],
 [{"id":"1","description":f"ZX{tag}","nextStep":[],"connectorLabel":[],"type":"Start"}],
 [{"id":"1","description":f"ZX{tag}","nextStep":[],"connectorLabel":[],"type":"Decision"}],
]:
    c,b=req(body)
    print(f"  type={body[0]['type']:10} -> {c} {b[:200].replace(chr(10),' ')}")
    if c=='200':
        d=json.loads(b); print(f"    *** ACCEPTED url={d.get('url','')[:110]}")
        open('/tmp/flow_url','w').write(d.get('url',''))
        break
