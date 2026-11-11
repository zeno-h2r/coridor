import json,subprocess,os
from collections import Counter
H=os.environ['H']; BB=os.environ['BB']
def get(path,tok):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}',H+path,'-H','token: '+tok,'-H',BB]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== does a LOW role get Superuser's permission set? ===")
for r in ['TESTER','EXTAUD','REVIEWER']:
    tok=open(f'/tmp/bac_{r}').read().strip()
    c,b=get('/api/v1/role_permissions?role_id=1',tok)
    try:
        rp=json.loads(b)['role_permissions']
        ids=Counter(x['role_id'] for x in rp)
        print(f"  {r:9} ?role_id=1 -> {c} rows={len(rp)} role_ids={dict(ids)}")
    except Exception as e:
        print(f"  {r:9} -> {c} {b[:120]}")
print()
print("=== what does Superuser's permission set reveal? (sample of granted perms) ===")
tok=open('/tmp/bac_TESTER').read().strip()
c,b=get('/api/v1/role_permissions?role_id=1',tok)
rp=json.loads(b)['role_permissions']
granted=[x for x in rp if x.get('value') in ('show','allow','edit','true')]
print(f"  total rows: {len(rp)}  granted-ish: {len(granted)}")
print("  sample granted keys:")
for x in granted[:12]:
    print(f"    {x['key']:34} section={str(x['section'])[:24]:26} value={x['value']}")
print()
print("=== compare: what TPU is denied (its own set) ===")
tpu=open('/tmp/bac_TPU').read().strip()
c,b=get('/api/v1/role_permissions',tpu)
rp2=json.loads(b)['role_permissions']
den=[x for x in rp2 if x.get('value')=='deny']
print(f"  TPU rows={len(rp2)} denied={len(den)}")
