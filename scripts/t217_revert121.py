import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
c,b=req('GET','/api/v1/issues/121')
i=json.loads(b)['issues'][0]
print("before revert:",i.get('status'))
c,b=req('PUT','/api/v1/issues/121',{"issue":{"status":"Inactive"}})
print("revert PUT:",c,b[:120].replace(chr(10),' '))
c,b=req('GET','/api/v1/issues/121')
i2=json.loads(b)['issues'][0]
print("after revert:",i2.get('status'))
print("created_at unchanged:",i2.get('created_at'))
