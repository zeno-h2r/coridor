import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TT=open('/tmp/tok_Tester').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or TT),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
def user(uid):
    c,b=req('GET',f'/api/v1/users/{uid}')
    try: return json.loads(b)['users'][0]
    except: return {}
print("=== why does 230 accept but other Owners 422? ===")
for uid in [230, 231, 5, 10, 11]:
    u=user(uid)
    if not u: print(f"  {uid} unreadable"); continue
    print(f"  {uid:>4} role={u.get('role_id')} auth={u.get('auth_type')} email={u.get('email')!r}")
print()
print("=== retry email write on 230 with full error detail ===")
c,b=req('PUT','/api/v1/users/230',{"user":{"email":"zeno0@bugcrowdninja.com"}})
print(f"  PUT -> {c}")
print(f"  {b[:400].replace(chr(10),' ')}")
print()
print("=== compare: 231 (Owner) same request ===")
c,b=req('PUT','/api/v1/users/231',{"user":{"email":"zeno0@bugcrowdninja.com"}})
print(f"  PUT -> {c}")
print(f"  {b[:400].replace(chr(10),' ')}")
