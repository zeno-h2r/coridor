import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(path):
    cmd=['curl','-s','-m','25',H+path,'-H','token: '+T,'-H',BB]
    return subprocess.run(cmd,capture_output=True,text=True).stdout
us=json.loads(req('/api/v1/users'))['users']
print("=== role 1 + role 2 accounts: auth_type and login-ability ===")
for u in us:
    if u.get('role_id') in (1,2):
        print(f"  {u['id']:3} role{u['role_id']} {str(u.get('auth_type')):20} {u['email'][:44]}")
