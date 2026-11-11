import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
def login(email,pw):
    cmd=['curl','-s','-m','30','-o','/tmp/l','-w','%{http_code}','-X','POST',H+'/api/v1/users/login',
         '-H',BB,'-H','Content-Type: application/json','-d',json.dumps({"credentials":{"email":email,"password":pw}})]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/l',encoding='utf-8',errors='replace').read()
cands=[("R2-301","jvolles@auditboard.com","TesterZx2026!"),
       ("R2-65","daniel@u1elhxrx.mailosaur.net","TesterZx2026!"),
       ("B-230","golden-leaf-3068@bugcrowdninja.com","Tester"),
       ("A-231","golden-snow-4771@bugcrowdninja.com","Tester")]
for label,email,pw in cands:
    c,b=login(email,pw)
    if c=='200':
        s=json.loads(b)['session']
        open(f'/tmp/tok_{label}','w').write(s['token'])
        print(f"  {label}: OK id={s['id']} role={s['role_id']} {s['email']}")
    else:
        print(f"  {label}: FAIL {c} {b[:100]}")
