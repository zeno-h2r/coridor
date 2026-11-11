import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
def req(m,p,body=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
def login(email,pw):
    cmd=['curl','-s','-m','25','-o','/tmp/l','-w','%{http_code}','-X','POST',H+'/api/v1/users/login',
         '-H',BB,'-H','Content-Type: application/json','-d',json.dumps({"credentials":{"email":email,"password":pw}})]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/l',encoding='utf-8',errors='replace').read()
print("=== find role-11 accounts ===")
c,b=req('GET','/api/v1/users')
us=json.loads(b)['users']
r11=[u for u in us if u.get('role_id')==11]
for u in r11:
    print(f"  id={u['id']} {u.get('email')} auth={u.get('auth_type')}")
print()
print("=== set a known password on 315 (role 11) ===")
c,b=req('PUT','/api/v1/users/315',{"user":{"password":"TesterZx2026!"}})
print(f"  PUT -> {c} {b[:120].replace(chr(10),' ')}")
req('PUT','/api/v1/users/315',{"user":{"requires_password_change":False}})
c,b=req('GET','/api/v1/users/315')
u=json.loads(b)['users'][0]
print(f"  email={u.get('email')!r} role={u.get('role_id')} req_pw={u.get('requires_password_change')}")
print()
print("=== login as TPU ===")
c,b=login(u['email'],"TesterZx2026!")
print(f"  login -> {c}")
if c=='200':
    s=json.loads(b)['session']
    open('/tmp/bac_TPU','w').write(s['token'])
    print(f"  OK id={s['id']} role={s['role_id']}")
else:
    print(f"  {b[:150]}")
