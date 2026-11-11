import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
TT=open('/tmp/bac_TPU').read().strip()
TO=open('/tmp/bac_OWNER').read().strip()
print("=== TPU: read a specific suggestion by id (Owner sees 111) ===")
for sid in [41,42,50,1]:
    c,b=req('GET',f'/api/v1/suggestions/{sid}',tok=TT)
    print(f"  TPU /suggestions/{sid} -> {c} {b[:140].replace(chr(10),' ')}")
print()
print("=== control: Owner reads the same ===")
for sid in [41,42]:
    c,b=req('GET',f'/api/v1/suggestions/{sid}',tok=TO)
    print(f"  OWNER /suggestions/{sid} -> {c} {b[:140].replace(chr(10),' ')}")
print()
print("=== full record of suggestion 41 (what's in it?) ===")
c,b=req('GET','/api/v1/suggestions/41',tok=TO)
try:
    d=json.loads(b)
    arr=d.get('suggestions') or []
    if arr:
        o=arr[0]
        for k,v in o.items():
            if isinstance(v,(str,int,float,bool,type(None))) and v not in ('',None):
                print(f"  {k:26} = {str(v)[:70]!r}")
except Exception as e: print("  ",c,b[:200])
