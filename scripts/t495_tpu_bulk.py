import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
TP=open('/tmp/bac_TPU').read().strip()
TO=open('/tmp/bac_OWNER').read().strip()
print("=== full 422 body from TPU (is it authz or processing?) ===")
body={"data":{"suggestionIds":[41],"createControlImpls":False,"programIds":[]}}
c,b=req('POST','/api/v1/suggestions/bulk-accept-with-control-implementation',body,tok=TP)
print(f"  {c}")
print(f"  {b[:900]}")
print()
print("=== same request as OWNER for comparison ===")
c,b=req('POST','/api/v1/suggestions/bulk-accept-with-control-implementation',body,tok=TO)
print(f"  {c}")
print(f"  {b[:900]}")
