import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def login(email,pw):
    cmd=['curl','-s','-m','30','-o','/tmp/l','-w','%{http_code}','-X','POST',H+'/api/v1/users/login',
         '-H',BB,'-H','Content-Type: application/json','-d',json.dumps({"credentials":{"email":email,"password":pw}})]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/l',encoding='utf-8',errors='replace').read()
# owner token alive?
c,b=login("golden-snow-4771@bugcrowdninja.com","Tester")
print("owner login:",c)
if c=='200':
    open('/tmp/owner_tok','w').write(json.loads(b)['session']['token'])
# role-2 accounts (already restored to TesterZx2026!)
for uid,email in [(301,'jvolles@auditboard.com'),(65,'daniel@u1elhxrx.mailosaur.net'),(316,'jhurt+admin@optro.ai')]:
    c,b=login(email,"TesterZx2026!")
    print(f"  {uid} {email[:38]:40} -> {c}")
    if c=='200':
        s=json.loads(b)['session']
        open(f'/tmp/r2_{uid}','w').write(s['token'])
        print(f"      role={s['role_id']}")
