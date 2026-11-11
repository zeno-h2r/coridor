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
    cmd=['curl','-s','-m','20','-o','/tmp/l','-w','%{http_code}','-X','POST',H+'/api/v1/users/login',
         '-H',BB,'-H','Content-Type: application/json','-d',json.dumps({"credentials":{"email":email,"password":pw}})]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/l',encoding='utf-8',errors='replace').read()
c,b=req('GET','/api/v1/users/231')
u=json.loads(b)['users'][0]
print(f"user 231: email={u.get('email')!r} role={u.get('role_id')} auth={u.get('auth_type')} req_pw={u.get('requires_password_change')}")
print()
PW="TesterZx2026!"
c,b=req('PUT','/api/v1/users/231',{"user":{"password":PW}})
print(f"  set password -> {c}")
req('PUT','/api/v1/users/231',{"user":{"requires_password_change":False}})
c,b=login(u['email'],PW)
print(f"  login -> {c}")
if c=='200':
    s=json.loads(b)['session']; open('/tmp/bac_OWNER','w').write(s['token'])
    print(f"  OK id={s['id']} role={s['role_id']} token saved")
else:
    print(f"  {b[:150]}")
