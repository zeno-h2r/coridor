import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
def login(email,pw):
    cmd=['curl','-s','-m','30','-o','/tmp/l','-w','%{http_code}','-X','POST',H+'/api/v1/users/login',
         '-H',BB,'-H','Content-Type: application/json','-d',json.dumps({"credentials":{"email":email,"password":pw}})]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/l',encoding='utf-8',errors='replace').read()
c,b=login("golden-snow-4771@bugcrowdninja.com","Tester")
print("owner login:",c)
if c=='200':
    s=json.loads(b)['session']; open('/tmp/tok_A','w').write(s['token'])
    print("  id",s['id'],"role",s['role_id'])
