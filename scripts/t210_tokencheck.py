import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def login(email,pw):
    cmd=['curl','-s','-m','30','-o','/tmp/l','-w','%{http_code}','-X','POST',H+'/api/v1/users/login',
         '-H',BB,'-H','Content-Type: application/json','-d',json.dumps({"credentials":{"email":email,"password":pw}})]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/l',encoding='utf-8',errors='replace').read()
c,b=login("golden-snow-4771@bugcrowdninja.com","Tester")
print("owner login:",c)
if c=='200':
    t=json.loads(b)['session']['token']
    open('/tmp/tok_owner','w').write(t)
    print("  token ok, id",json.loads(b)['session']['id'])
