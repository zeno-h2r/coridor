import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_OWNER').read().strip()
tag='ZXF'+uuid.uuid4().hex[:5]
def raw(pay):
    cmd=['curl','-s','-i','-m','25','-X','POST',H+'/api/v1/risks',
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System','-d',json.dumps({"risk":{"name":pay}})]
    return subprocess.run(cmd,capture_output=True,text=True).stdout
r=raw(f'plain{tag}')
for line in r.splitlines():
    l=line.lower()
    if l.startswith('content-security-policy:') and 'report-only' not in l:
        print("=== ENFORCED CSP ===")
        print(line[:1200])
print()
print("=== analysis ===")
csp=[l for l in r.splitlines() if l.lower().startswith('content-security-policy:') and 'report-only' not in l.lower()]
if csp:
    c=csp[0]
    checks={
      "script-src *": "script-src *" in c,
      "'unsafe-inline' in script-src": "script-src * 'unsafe-inline'" in c,
      "'unsafe-eval' in script-src": "'unsafe-eval'" in c,
      "object-src missing": "object-src" not in c,
      "base-uri missing": "base-uri" not in c,
      "default-src *": "default-src *" in c,
      "frame-ancestors 'self'": "frame-ancestors 'self'" in c,
    }
    for k,v in checks.items(): print(f"  {k:34} {v}")
