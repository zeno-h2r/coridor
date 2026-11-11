import json,subprocess,os
from collections import Counter
H=os.environ['H']; BB=os.environ['BB']
def get(p,tok):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}',H+p,'-H','token: '+tok,'-H',BB]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== populated resources: row counts by role ===")
RES=['audit_surveys','bookings','project_plans','financial_applications','skills']
for p in RES:
    row=[]
    for r in ['OWNER','TESTER','TPU']:
        tok=open(f'/tmp/bac_{r}').read().strip()
        c,b=get('/api/v1/'+p,tok)
        n=0
        try:
            d=json.loads(b)
            for k in d:
                if isinstance(d[k],list): n=len(d[k])
        except: pass
        row.append(f"{r}={c}/{n}")
    print(f"  {p:26} " + "  ".join(row))
print()
print("=== audit_surveys detail (has real rows) ===")
tok=open('/tmp/bac_TESTER').read().strip()
c,b=get('/api/v1/audit_surveys',tok)
d=json.loads(b)['audit_surveys']
print(f"  Tester sees {len(d)}")
for s in d[:4]:
    print(f"    id={s.get('id')} name={str(s.get('name'))[:40]!r} status={s.get('status')} perms={json.dumps(s.get('_permissions'))[:80]}")
