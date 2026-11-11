import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TO=open('/tmp/bac_OWNER').read().strip()
TP=open('/tmp/bac_TPU').read().strip()
TT=open('/tmp/bac_TESTER').read().strip()
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== real suggestion ids on narrative 38 ===")
c,b=req('GET','/api/v1/suggestions',tok=TO)
sug=json.loads(b)['suggestions']
n38=[s for s in sug if s.get('suggestable_id')==38]
print(f"  narrative 38 has {len(n38)} suggestions; ids: {[s['id'] for s in n38][:6]}")
sid=n38[0]['id']
print(f"  using suggestion id {sid} (suggested {n38[0].get('suggested_type')}#{n38[0].get('suggested_id')})")
print()
print("=== the exact request, all three roles ===")
body={"data":{"suggestionIds":[sid],"createControlImpls":False,"programIds":[]}}
print(f"  BODY: {json.dumps(body)}")
print()
for r,tok in [('OWNER(5)',TO),('TESTER(4)',TT),('TPU(11)',TP)]:
    c,b=req('POST','/api/v1/suggestions/bulk-accept-with-control-implementation',body,tok=tok)
    print(f"  {r:11} -> {c}")
    print(f"     {b[:260].replace(chr(10),' ')}")
    print()
