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
c,b=req('GET','/api/v1/users/53')
u=json.loads(b)['users'][0]
print("53 state: role",u['role_id'],"auth",u['auth_type'],"req_pw",u['requires_password_change'])
print("\nwhy did my restore 422? full error:")
c,b=req('PUT','/api/v1/users/53',{"user":{"password":"Tester"}})
print("  ",c,b[:350])
print("\ntry restore with the role-2 token (self-edit):")
c,b=login(EMAIL,"Zx9!chain47")
print("  re-login as 53 ->",c)
if c=='200':
    RT=json.loads(b)['session']['token']
    c2,b2=req('PUT','/api/v1/users/53',{"user":{"password":"Tester"}},tok=RT)
    print("  self restore ->",c2,b2[:200].replace(chr(10),' '))
    c3,b3=login(EMAIL,"Tester")
    print("  login with Tester ->",c3)
