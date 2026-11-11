import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
TO=open('/tmp/bac_OWNER').read().strip()
TT=open('/tmp/bac_TESTER').read().strip()
TP=open('/tmp/bac_TPU').read().strip()
print("=== crack suggestions/bulk-accept shape (500 = shape, not gate) ===")
shapes=[
 {},
 {"ids":[41]},
 {"suggestion_ids":[41]},
 {"suggestions":[{"id":41}]},
 {"ids":[41],"status":"accepted"},
 {"suggestions":[{"id":41,"status":"accepted"}]},
]
for s in shapes:
    c,b=req('POST','/api/v1/suggestions/bulk-accept',s,tok=TO)
    print(f"  {json.dumps(s)[:56]:58} -> {c} {b[:130].replace(chr(10),' ')}")
print()
print("=== and bulk-reject ===")
for s in [{"ids":[41]},{"suggestion_ids":[41]},{"suggestions":[{"id":41}]}]:
    c,b=req('POST','/api/v1/suggestions/bulk-reject',s,tok=TO)
    print(f"  {json.dumps(s)[:56]:58} -> {c} {b[:130].replace(chr(10),' ')}")
