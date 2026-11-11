import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
for p,b in [('/api/v1/issues/121/amend',{}),
            ('/api/v1/issues/121/amend',{"issue":{"status":"Inactive"}}),
            ('/api/v1/issues/121/amend',{"status":"Inactive"}),
            ('/api/v1/issues/121/amend',{"issue":{"status":"Inactive"},"amend_reason":"revert test artifact"})]:
    c,t=req('POST',p,b)
    print(f"  {c} POST {p} {json.dumps(b)[:60]} -> {t[:170].replace(chr(10),' ')}")
c,b=req('GET','/api/v1/issues/121')
print("\n  status now:",json.loads(b)['issues'][0].get('status'))
