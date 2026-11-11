import json,subprocess,os
from collections import Counter
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-AuditBoard-Source: SchemaTable Rows']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
# direct list has role_id + auth_type together
c,b=req('GET','/api/v1/users')
us=json.loads(b)['users']
print("users:",len(us))
c2=Counter((u.get('auth_type'),u.get('role_id')) for u in us)
print("\nauth_type x role:")
for (t,r),v in sorted(c2.items(), key=lambda x:-x[1]):
    print(f"   {str(t):20} role {str(r):3} -> {v}")
pw=[u for u in us if u.get('auth_type')=='password']
print(f"\n>>> ATO-able (auth_type=password): {len(pw)} of {len(us)}")
print("   by role:", dict(Counter(u.get('role_id') for u in pw)))
json.dump([(u['id'],u.get('email'),u.get('role_id')) for u in pw],open('state/ato_able.json','w'),indent=1)
print("\n   sample:",[(u['id'],u.get('email'),u.get('role_id')) for u in pw[:5]])
