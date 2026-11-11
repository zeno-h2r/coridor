import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
c,b=req('GET','/api/v1/users')
print("GET /users ->",c,"len",len(b))
d=json.loads(b)
print("keys:",list(d.keys()))
us=d.get('users') or []
print("count:",len(us))
byrole={}
for u in us:
    byrole.setdefault(u.get('role_id'),[]).append((u['id'],u.get('email')))
for r in sorted(byrole, key=lambda x:(x is None,x)):
    print(f"  role {r}: {len(byrole[r])} users  e.g. {byrole[r][:3]}")
json.dump({str(k):v for k,v in byrole.items()},open('state/users_by_role.json','w'),indent=1)
