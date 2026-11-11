import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
def login(email,pw):
    cmd=['curl','-s','-m','25','-o','/tmp/l','-w','%{http_code}','-X','POST',H+'/api/v1/users/login',
         '-H',BB,'-H','Content-Type: application/json','-d',json.dumps({"credentials":{"email":email,"password":pw}})]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/l',encoding='utf-8',errors='replace').read()
cands=[
 ("OWNER","golden-snow-4771@bugcrowdninja.com",["Tester","TesterZx2026!","Zx9!lower47"]),
 ("TPU","zx-6db21a8623@bugcrowdninja.com",["Tester","TesterZx2026!","Zx9!lower47"]),
 ("TPU2","analyst+member@bugcrowdanalyst.com",["Tester","TesterZx2026!","Zx9!lower47"]),
]
for label,email,pws in cands:
    for pw in pws:
        c,b=login(email,pw)
        if c=='200':
            s=json.loads(b)['session']
            key = 'TPU' if label.startswith('TPU') else label
            open(f'/tmp/bac_{key}','w').write(s['token'])
            print(f"  {label:8} OK id={s['id']} role={s['role_id']} pw={pw}")
            break
    else:
        print(f"  {label:8} FAIL all")
