import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
def login(email,pw):
    cmd=['curl','-s','-m','20','-o','/tmp/l','-w','%{http_code}','-X','POST',H+'/api/v1/users/login',
         '-H',BB,'-H','Content-Type: application/json','-d',json.dumps({"credentials":{"email":email,"password":pw}})]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/l',encoding='utf-8',errors='replace').read()
cands=[
 ("OWNER","golden-snow-4771@bugcrowdninja.com","TesterZx2026!"),
 ("OWNER","golden-snow-4771@bugcrowdninja.com","Tester"),
 ("SYSADMIN","zx-sysadm-66650c74@bugcrowdninja.com","TesterZx2026!"),
 ("TESTER","tester@soxhub.com","Zx9!lower47"),
 ("TPU","zx-6db21a8623@bugcrowdninja.com","TesterZx2026!"),
 ("B230","zeno0@bugcrowdninja.com","TesterZx2026!"),
]
for label,email,pw in cands:
    c,b=login(email,pw)
    if c=='200':
        s=json.loads(b)['session']
        print(f"  OK   {label:9} {email:42} pw={pw:16} id={s['id']} role={s['role_id']}")
    else:
        print(f"  FAIL {label:9} {email:42} pw={pw:16} {c}")
