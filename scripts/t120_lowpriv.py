import json,subprocess,os,random
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or T),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
# list roles to pick a low-priv one
c,b=req('GET','/api/v1/roles')
for r in json.loads(b)['roles']:
    print(f"  role {r['id']:2} {r['name']:22} limited={r.get('is_limited')} implementer={r.get('is_implementer')}")
