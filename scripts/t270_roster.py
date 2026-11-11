import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
def login(email,pw):
    cmd=['curl','-s','-m','30','-o','/tmp/l','-w','%{http_code}','-X','POST',H+'/api/v1/users/login',
         '-H',BB,'-H','Content-Type: application/json','-d',json.dumps({"credentials":{"email":email,"password":pw}})]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/l',encoding='utf-8',errors='replace').read()
c,b=login("golden-snow-4771@bugcrowdninja.com","Tester")
if c!='200': raise SystemExit(f"owner login failed {c}")
T=json.loads(b)['session']['token']; open('/tmp/tok_A','w').write(T)
print("owner 231 OK")
def get(p):
    cmd=['curl','-s','-m','40',H+p,'-H','token: '+T,'-H',BB]
    return subprocess.run(cmd,capture_output=True,text=True).stdout
us=json.loads(get('/api/v1/users'))['users']
ROLE={1:'Superuser',2:'System Admin',3:'Reviewer',4:'Tester',5:'Owner',6:'External Auditor',11:'Third Party User'}
from collections import defaultdict
by=defaultdict(list)
for u in us:
    if u.get('auth_type')=='password':
        by[u.get('role_id')].append((u['id'],u.get('email')))
print("\nlogin-enabled (auth_type=password) by role:")
for r in sorted(by):
    print(f"  role {r} ({ROLE.get(r,'?')}): {len(by[r])} accounts")
    for x in by[r][:4]: print("     ",x)
json.dump({str(k):v for k,v in by.items()},open('state/login_by_role.json','w'),indent=1)
