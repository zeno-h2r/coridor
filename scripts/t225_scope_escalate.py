import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TA=open('/tmp/tok_A-231').read().strip()
TB=open('/tmp/tok_B-230').read().strip()
NID=open('/tmp/b_narr').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or TA),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== A(231) tries to add itself to 230's narrative scope ===")
attempts=[
 ("scopes.owner_users.all",{"narrative":{"scopes":{"owner_users":{"all":[230,231]}}}}),
 ("scopes merge",{"narrative":{"scopes":{"owner_users":{"all":[230,231]},"owner_teams":{}}}}),
 ("scope_users",{"narrative":{"scope_users":[230,231]}}),
 ("owner_users",{"narrative":{"owner_users":[230,231]}}),
]
for label,body in attempts:
    c,b=req('PUT',f'/api/v1/narratives/{NID}',body,tok=TA)
    print(f"  {label:24} -> {c} {b[:150].replace(chr(10),' ')}")
print()
print("=== check current scope after attempts ===")
c,b=req('GET',f'/api/v1/narratives/{NID}',tok=TB)
n=json.loads(b)['narratives'][0]
print("  scopes:",json.dumps(n.get('scopes'))[:250])
print()
print("=== A(231) can it DELETE 230's narrative? ===")
c,b=req('DELETE',f'/api/v1/narratives/{NID}',tok=TA)
print(f"  DELETE -> {c} {b[:200].replace(chr(10),' ')}")
print()
print("=== A(231) document_version plane on 230's narrative (doc 1402) ===")
for p in [f'/api/v1/document_versions/1402', f'/api/v1/narratives/{NID}/document_versions']:
    c,b=req('GET',p,tok=TA)
    print(f"  {c} GET {p}  {b[:150].replace(chr(10),' ')}")
