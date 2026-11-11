import json,subprocess,os
from collections import Counter
H=os.environ['H']; BB=os.environ['BB']
def get(path,tok):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}',H+path,'-H','token: '+tok,'-H',BB]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== role_permissions scoping: does each role only see its own? ===")
for r in ['OWNER','SYSADMIN','REVIEWER','TESTER','EXTAUD','TPU']:
    try: tok=open(f'/tmp/bac_{r}').read().strip()
    except: continue
    c,b=get('/api/v1/role_permissions',tok)
    if c!='200': print(f"  {r:9} {c}"); continue
    try:
        rp=json.loads(b)['role_permissions']
        roles=Counter(x['role_id'] for x in rp)
        print(f"  {r:9} {c} rows={len(rp):>5} role_ids={dict(roles)}")
    except Exception as e: print(f"  {r:9} parse err")
print()
print("=== can a role request ANOTHER role's permissions via filter? ===")
OWN=open('/tmp/bac_OWNER').read().strip()
for q in ['?filter[role_id][eq]=1','?filter[role_id][eq]=2','?role_id=1','?filter[roleId][eq]=1']:
    c,b=get('/api/v1/role_permissions'+q,OWN)
    n=0; ids={}
    try:
        rp=json.loads(b)['role_permissions']; n=len(rp); ids=dict(Counter(x['role_id'] for x in rp))
    except: pass
    print(f"  OWNER {q:28} -> {c} rows={n} role_ids={ids}")
