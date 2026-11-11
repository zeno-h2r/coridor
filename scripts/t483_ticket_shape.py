import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
TO=open('/tmp/bac_OWNER').read().strip()
print("=== get full required shape for ticketing/tickets ===")
c,b=req('POST','/api/v1/ticketing/tickets',{"credential_id":1,"ab_resource_type":"taskItem"},tok=TO)
print(f"  {c}")
print(f"  {b[:700]}")
print()
print("=== are there any ticketing credentials configured? ===")
for p in ['/api/v1/ticketing/projects','/api/v1/ticketing/ab_resource_types','/api/v1/ticketing/tickets/types']:
    c,b=req('GET',p,tok=TO)
    print(f"  {c} {p}  {b[:200].replace(chr(10),' ')}")
