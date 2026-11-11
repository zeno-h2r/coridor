import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or T),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== restore victim 230 password to program-issued 'Tester' ===")
c,b=req('PUT','/api/v1/users/230',{"user":{"password":"Tester"}})
print("  ->",c,b[:250].replace(chr(10),' '))
c,b=req('PUT','/api/v1/users/230',{"user":{"requires_password_change":False}})
print("  flag clear ->",c)
