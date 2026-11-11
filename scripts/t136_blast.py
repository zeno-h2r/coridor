import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def post(path,body):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-AuditBoard-Source: SchemaTable Rows','-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
c,b=post('/api/v1/table/query?entities=user',{"ab:query":{"entities":["user"],"filter":{},"include":["user"]}})
d=json.loads(b); inc=d.get('included') or []
print("total users:",len(inc))
from collections import Counter
at=Counter(); atrole=Counter()
for u in inc:
    a=u.get('attributes') or {}
    t=a.get('authType'); r=a.get('roleId')
    at[t]+=1
    atrole[(t,r)]+=1
print("\nauth_type distribution:")
for k,v in at.most_common(): print(f"   {k!s:12} {v}")
print("\nlogin-enabled (auth_type=password) by role:")
for (t,r),v in sorted(atrole.items(), key=lambda x:-x[1]):
    if t=='password': print(f"   role {r:2}: {v} accounts")
pw=[u for u in inc if (u.get('attributes') or {}).get('authType')=='password']
print(f"\n>>> ATO-able accounts (auth_type=password): {len(pw)} of {len(inc)}")
json.dump([(u['id'],(u.get('attributes') or {}).get('email'),(u.get('attributes') or {}).get('roleId')) for u in pw],
          open('state/ato_able.json','w'),indent=1)
