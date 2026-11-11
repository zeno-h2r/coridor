import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
def req(m,p,body=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='ZXE'+uuid.uuid4().hex[:5]
print("=== inject into exception 32 writable fields (SysAdmin) ===")
fields=['title','description','closure_notes','recommendation','business_unit']
for f in fields:
    pay=f'<b>ZX{tag}</b>'
    c,b=req('PUT','/api/v1/exception_requests/32',{"exception_request":{f:pay}})
    c2,b2=req('GET','/api/v1/exception_requests/32')
    stored=None
    try: stored=json.loads(b2)['exception_requests'][0].get(f)
    except: pass
    enc = '&lt;' in str(stored) if stored else None
    raw = pay in str(stored) if stored else False
    print(f"  {f:16} PUT={c}  stored={str(stored)[:50]!r}  ENCODED={enc} RAW={raw}")
