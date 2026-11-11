import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TA=open('/tmp/tok_A').read().strip()
PW="Zx9!lower47"
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or TA),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
def login(email,pw):
    cmd=['curl','-s','-m','30','-o','/tmp/l','-w','%{http_code}','-X','POST',H+'/api/v1/users/login',
         '-H',BB,'-H','Content-Type: application/json','-d',json.dumps({"credentials":{"email":email,"password":pw}})]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/l',encoding='utf-8',errors='replace').read()
ROLE={3:'Reviewer',4:'Tester',6:'External Auditor'}
targets=[(15,'jim@soxhub.com',3),(171,'reviewer@soxhub.com',3),
         (170,'tester@soxhub.com',4),(313,'analyst+tester@bugcrowdanalyst.com',4),
         (172,'external@soxhub.com',6),(52,'mchan@soxhub.com',6)]
print(f"{'id':>4} {'role':18} {'email':32} {'PUT':>5} {'login':>6}")
for uid,email,role in targets:
    c,b=req('PUT',f'/api/v1/users/{uid}',{"user":{"password":PW}})
    line=f"{uid:>4} {ROLE[role]:18} {email[:30]:32} {c:>5}"
    if c=='200':
        req('PUT',f'/api/v1/users/{uid}',{"user":{"requires_password_change":False}})
        c2,b2=login(email,PW)
        line+=f" {c2:>6}"
        if c2=='200':
            s=json.loads(b2)['session']
            line+=f"  *** TAKEN role={s['role_id']} ***"
            open(f'/tmp/tok_{ROLE[role].replace(" ","")}','w').write(s['token'])
            open(f'/tmp/taken_{uid}','w').write(email)
    print(line)
