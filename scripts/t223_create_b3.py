import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TB=open('/tmp/tok_B-230').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or TB),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== issue with category/ident ===")
for body in [
 {"issue":{"title":"ZX-B-OWNED-CONTENT","description":"owned by user 230","status":"Open",
           "issue_category_id":1,"issue_ident_id":1}},
 {"issue":{"title":"ZX-B-OWNED-CONTENT","description":"owned by user 230","status":"Open",
           "issue_category":1,"issue_ident":1}},
]:
    c,b=req('POST','/api/v1/issues',body)
    print(f"  {list(body['issue'].keys())[-2:]} -> {c} {b[:250].replace(chr(10),' ')}")
    if c in ('200','201'):
        try:
            i=json.loads(b)['issues'][0]
            print(f"    created id={i['id']} creator={i.get('creator_user_id')} owner={i.get('owner_id')}")
            open('/tmp/b_issue','w').write(str(i['id']))
        except: pass
        break
print()
print("=== narrative with name field ===")
for body in [
 {"narrative":{"name":"ZX-B-NARRATIVE","uid":"zx-b-narr-1","body":"owned by 230"}},
 {"narrative":{"title":"ZX-B-NARRATIVE","name":"ZX-B-NARRATIVE","uid":"zx-b-narr-2"}},
]:
    c,b=req('POST','/api/v1/narratives',body)
    print(f"  {list(body['narrative'].keys())} -> {c} {b[:250].replace(chr(10),' ')}")
    if c in ('200','201'):
        try:
            n=json.loads(b)['narratives'][0]
            print(f"    created id={n['id']} name={n.get('name')!r} creator={n.get('creator_user_id')}")
            open('/tmp/b_narr','w').write(str(n['id']))
        except: pass
        break
