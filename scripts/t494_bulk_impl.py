import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
TO=open('/tmp/bac_OWNER').read().strip()
TT=open('/tmp/bac_TESTER').read().strip()
TP=open('/tmp/bac_TPU').read().strip()
print("=== bulk-accept-with-control-implementation (exact shape) ===")
body={"data":{"suggestionIds":[41],"createControlImpls":False,"programIds":[]}}
for r,tok in [('OWNER',TO),('TESTER',TT),('TPU',TP)]:
    c,b=req('POST','/api/v1/suggestions/bulk-accept-with-control-implementation',body,tok=tok)
    print(f"  {r:9} -> {c} {b[:200].replace(chr(10),' ')}")
print()
print("=== also try the plain bulk-accept with the same data envelope ===")
for r,tok in [('OWNER',TO),('TPU',TP)]:
    c,b=req('POST','/api/v1/suggestions/bulk-accept',body,tok=tok)
    print(f"  {r:9} bulk-accept -> {c} {b[:200].replace(chr(10),' ')}")
