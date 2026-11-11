import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
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
EMAIL="steve@u1elhxrx.mailosaur.net"
FINAL="TesterZx2026!"
c,b=req('PUT','/api/v1/users/53',{"user":{"password":FINAL}})
print("set documented pw ->",c, b[:150].replace(chr(10),' '))
req('PUT','/api/v1/users/53',{"user":{"requires_password_change":False}})
c,b=login(EMAIL,FINAL)
print("login ->",c)
print()
print("=== FINAL STATE CHECK ===")
for uid in [230,315,53]:
    c,b=req('GET',f'/api/v1/users/{uid}')
    u=json.loads(b)['users'][0]
    print(f"  {uid:3} {u['email'][:40]:42} role={u['role_id']} auth={u['auth_type']} req_pw={u['requires_password_change']}")
