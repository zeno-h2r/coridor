import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
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
for uid in [17,18]:
    c,b=req('GET',f'/api/v1/users/{uid}')
    u=json.loads(b)['users'][0]
    print(f"user {uid} {u['email']}: role={u['role_id']} req_pw_change={u['requires_password_change']} updated={u['updated_at']}")
    for label,pw in [("attacker pw","Zx9!sysadm47"),("program 'Tester'","Tester")]:
        c2,b2=login(u['email'],pw)
        print(f"   login {label:16} -> {c2} {b2[:90].replace(chr(10),' ')}")
    print()
