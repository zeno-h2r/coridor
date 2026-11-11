import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,hdr=None,body=None):
    cmd=['curl','-s','-m','25','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H',BB,'-H','Content-Type: application/json','-H','Accept: application/vnd.api+json']
    if hdr:
        for k,v in hdr.items(): cmd+=['-H',f'{k}: {v}']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
paths=['/api/v2/auth','/api/v2/auditable-entity','/api/v2/auditable-entity/coverage-roll-up',
       '/api/v2/auditable-entity/relationship-count','/api/v2/ml-trace/1','/api/v2/user/231/avatar',
       '/api/v2/user/1/avatar','/api/v2/users','/api/v2/me']
print("=== /api/v2 with v1 session token as TOKEN ===")
for p in paths:
    c,t=req('GET',p,hdr={'TOKEN':T})
    print(f"  {c} GET {p:46} {t[:130].replace(chr(10),' ')}")
print("\n=== does TOKEN accept a bearer-style value? ===")
for label,v in [("Bearer <tok>","Bearer "+T),("raw hex","b03074101e72781a78e8e1d8eadea2ebf1682ccc"),
                ("231:hex",T),("jwt-ish","eyJhbGciOiJIUzI1NiJ9.e30.x")]:
    c,t=req('GET','/api/v2/auth',hdr={'TOKEN':v})
    print(f"  {label:16} -> {c} {t[:120].replace(chr(10),' ')}")
