import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
EMAIL="zeno0+lowpriv@bugcrowdninja.com"; PW="LowPriv!2026zx"
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or T),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
body={"user":{"email":EMAIL,"first_name":"Zx","last_name":"LowPriv","role_id":11,
              "password":PW,"requires_password_change":False,"scim_user_active":"true"}}
c,b=req('POST','/api/v1/users',body)
print("CREATE role11 ->",c)
print("  ",b[:400].replace(chr(10),' '))
if c in ('200','201'):
    try:
        u=json.loads(b)['users'][0]
        print("  new id:",u['id'],"role:",u['role_id'])
        open('/tmp/lowid','w').write(str(u['id']))
    except Exception as e: print("  parse",e)
