import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def login(email,pw):
    cmd=['curl','-s','-m','30','-o','/tmp/l','-w','%{http_code}','-X','POST',H+'/api/v1/users/login',
         '-H',BB,'-H','Content-Type: application/json','-d',json.dumps({"credentials":{"email":email,"password":pw}})]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/l',encoding='utf-8',errors='replace').read()
for label,email,pw in [("owner","golden-snow-4771@bugcrowdninja.com","Tester"),
                       ("r2-301","jvolles@auditboard.com","TesterZx2026!"),
                       ("r2-65","daniel@u1elhxrx.mailosaur.net","TesterZx2026!")]:
    c,b=login(email,pw)
    if c=='200':
        s=json.loads(b)['session']
        open(f'/tmp/tok_{label}','w').write(s['token'])
        print(f"  {label:8} OK id={s['id']} role={s['role_id']}")
    else:
        print(f"  {label:8} FAIL {c} {b[:80]}")
