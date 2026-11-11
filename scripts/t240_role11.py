import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
def login(email,pw):
    cmd=['curl','-s','-m','30','-o','/tmp/l','-w','%{http_code}','-X','POST',H+'/api/v1/users/login',
         '-H',BB,'-H','Content-Type: application/json','-d',json.dumps({"credentials":{"email":email,"password":pw}})]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/l',encoding='utf-8',errors='replace').read()
# role 11 limited third-party user
for label,email,pw in [("R11-315","analyst+member@bugcrowdanalyst.com","Tester"),
                       ("B-230","golden-leaf-3068@bugcrowdninja.com","Tester"),
                       ("A-231","golden-snow-4771@bugcrowdninja.com","Tester")]:
    c,b=login(email,pw)
    if c=='200':
        s=json.loads(b)['session']
        open(f'/tmp/tok_{label}','w').write(s['token'])
        print(f"  {label}: OK id={s['id']} role={s['role_id']} {s['email']}")
    else:
        print(f"  {label}: FAIL {c} {b[:120]}")
