import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def login(email,pw):
    cmd=['curl','-s','-m','30','-o','/tmp/l','-w','%{http_code}','-X','POST',H+'/api/v1/users/login',
         '-H',BB,'-H','Content-Type: application/json','-d',json.dumps({"credentials":{"email":email,"password":pw}})]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/l',encoding='utf-8',errors='replace').read()
for label,email in [("A","golden-snow-4771@bugcrowdninja.com"),("B","golden-leaf-3068@bugcrowdninja.com")]:
    c,b=login(email,"Tester")
    if c=='200':
        s=json.loads(b)['session']
        open(f'/tmp/tok_{label}','w').write(s['token'])
        print(f"  {label}={s['id']} role={s['role_id']} {s['email']}")
    else: print(f"  {label} FAIL {c}")
