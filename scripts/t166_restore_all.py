import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
def login(email,pw):
    cmd=['curl','-s','-m','30','-o','/tmp/l','-w','%{http_code}','-X','POST',H+'/api/v1/users/login',
         '-H',BB,'-H','Content-Type: application/json','-d',json.dumps({"credentials":{"email":email,"password":pw}})]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/l',encoding='utf-8',errors='replace').read()
FINAL="TesterZx2026!"
targets=[(65,'daniel@u1elhxrx.mailosaur.net'),(123,'jim@u1elhxrx.mailosaur.net'),
         (301,'jvolles@auditboard.com'),(307,'juanadmin@email.com'),
         (308,'jhurt+test2@auditboard.com'),(316,'jhurt+admin@optro.ai')]
for uid,email in targets:
    c,b=req('PUT',f'/api/v1/users/{uid}',{"user":{"password":FINAL}})
    req('PUT',f'/api/v1/users/{uid}',{"user":{"requires_password_change":False}})
    c2,b2=login(email,FINAL)
    print(f"  {uid:3} {email[:40]:42} set={c} login={c2}")
