import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
c,b=req('PUT','/api/v1/users/1',{"user":{"password":"Zx9!su47test"}})
print("Superuser 422 full detail:")
print(" ",b[:400])
print()
# find low-priv users
c,b=req('POST','/api/v1/table/query?entities=user',{"ab:query":{"entities":["user"],"filter":{},"include":["user"]}})
d=json.loads(b); inc=d.get('included') or []
byrole={}
for u in inc:
    a=u.get('attributes') or {}
    byrole.setdefault(a.get('roleId'),[]).append((u['id'],a.get('email')))
for r in sorted(byrole, key=lambda x:(x is None,x)):
    print(f"  role {r}: {len(byrole[r])} users  e.g. {byrole[r][:3]}")
