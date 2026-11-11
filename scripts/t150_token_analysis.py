import json,subprocess,os,hashlib
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def login(email,pw):
    cmd=['curl','-s','-m','30','-o','/tmp/l','-w','%{http_code}','-X','POST',H+'/api/v1/users/login',
         '-H',BB,'-H','Content-Type: application/json','-d',json.dumps({"credentials":{"email":email,"password":pw}})]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/l',encoding='utf-8',errors='replace').read()
E="golden-snow-4771@bugcrowdninja.com"
toks=[]
for i in range(3):
    c,b=login(E,"Tester")
    if c=='200':
        t=json.loads(b)['session']['token']
        toks.append(t)
        print(f"login {i+1}: {t}")
    else:
        print(f"login {i+1}: {c} {b[:100]}")
print("\nDETERMINISTIC?" , "YES - same token every login" if len(set(toks))==1 else f"NO - {len(set(toks))} distinct tokens")
if toks:
    uid,hexpart=toks[0].split(':')
    print(f"\nuser_id={uid}  hexpart={hexpart}  len={len(hexpart)}")
    cands={
      'sha1(email)':E, 'sha1(uid)':uid, 'sha1(uid:email)':f"{uid}:{E}",
      'sha1(email:pw)':f"{E}:Tester", 'sha1(pw)':"Tester",
      'sha1(uid:email:pw)':f"{uid}:{E}:Tester", 'sha1(lower email)':E.lower(),
      'sha1(Tester:email)':f"Tester:{E}",
    }
    print("\nhash candidates:")
    for name,s in cands.items():
        h=hashlib.sha1(s.encode()).hexdigest()
        print(f"  {name:22} {h}  {'*** MATCH ***' if h==hexpart else ''}")
