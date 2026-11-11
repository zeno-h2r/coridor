import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(path):
    cmd=['curl','-s','-m','25',H+path,'-H','token: '+T,'-H',BB]
    return subprocess.run(cmd,capture_output=True,text=True).stdout
for uid in [17,18,230,231,315]:
    try:
        u=json.loads(req(f'/api/v1/users/{uid}'))['users'][0]
        print(f"  {uid:3} role={u['role_id']:2} auth_type={u.get('auth_type')!s:10} login_attempt={u.get('login_attempt')} email={u['email']}")
    except Exception as e: print(uid,"err",e)
