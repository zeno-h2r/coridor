import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
# closed issues need a reopen path; try common ones
for p,b in [('/api/v1/issues/121/reopen',{}),
            ('/api/v1/issues/121',{"issue":{"status":"Open","cancel_reason":None}}),
            ('/api/v1/issues/121',{"issue":{"status":"Inactive"},"force":True}),
            ('/api/v1/issues/121/ethereal_update',{"issue":{"status":"Inactive"}})]:
    c,t=req('PUT' if 'ethereal' not in p else 'POST',p,b)
    print(f"  {c} {p:44} {t[:150].replace(chr(10),' ')}")
c,b=req('GET','/api/v1/issues/121')
print("\n  status now:",json.loads(b)['issues'][0].get('status'))
