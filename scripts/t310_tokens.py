import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
def login(email,pw):
    cmd=['curl','-s','-m','25','-o','/tmp/l','-w','%{http_code}','-X','POST',H+'/api/v1/users/login',
         '-H',BB,'-H','Content-Type: application/json','-d',json.dumps({"credentials":{"email":email,"password":pw}})]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/l',encoding='utf-8',errors='replace').read()
cands=[
 ("OWNER","golden-snow-4771@bugcrowdninja.com","TesterZx2026!"),
 ("SYSADMIN","zx-sysadm-66650c74@bugcrowdninja.com","TesterZx2026!"),
 ("TESTER","tester@soxhub.com","Zx9!lower47"),
 ("REVIEWER","zx-cb11aa297f@bugcrowdninja.com","Zx9!lower47"),
 ("EXTAUD","zx-8b4f81ab10@bugcrowdninja.com","Zx9!lower47"),
 ("TPU","zx-6db21a8623@bugcrowdninja.com","Tester"),
]
ok=0
for label,email,pw in cands:
    c,b=login(email,pw)
    if c=='200':
        s=json.loads(b)['session']
        open(f'/tmp/bac_{label}','w').write(s['token'])
        print(f"  {label:9} OK id={s['id']:>3} role={s['role_id']:>2}")
        ok+=1
    else: print(f"  {label:9} FAIL {c}")
print(f"\n{ok}/6 live")
