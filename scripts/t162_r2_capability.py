import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
R2=open('/tmp/tok301').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or T),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== capabilities: Owner(231) vs SystemAdmin(301) ===")
tests=[
 ('GET','/api/v1/settings',None),
 ('GET','/api/v1/roles',None),
 ('GET','/api/v1/usage/totals',None),
 ('GET','/api/v1/webhook_urls',None),
 ('GET','/api/v1/assistant_knowledge_files',None),
 ('GET','/api/v1/ml_generative_prompts',None),
 ('GET','/api/v1/tiering_rules',None),
 ('POST','/api/v1/users',{"user":{"email":"zx-probe@bugcrowdninja.com","first_name":"Zx","last_name":"P","role_id":11}}),
 ('PUT','/api/v1/users/230',{"user":{"job_title":"zx"}}),
 ('PUT','/api/v1/users/1',{"user":{"job_title":"zx"}}),
]
print(f"  {'endpoint':46} {'Owner':>6} {'SysAdmin':>9}")
for m,p,b in tests:
    c1,_=req(m,p,b,tok=T)
    c2,_=req(m,p,b,tok=R2)
    flag='  <<< DIFF' if c1!=c2 else ''
    print(f"  {m+' '+p[:40]:46} {c1:>6} {c2:>9}{flag}")
