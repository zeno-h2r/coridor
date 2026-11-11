import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TB=open('/tmp/tok_B-230').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or TB),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== B(230) creates an issue ===")
c,b=req('POST','/api/v1/issues',{"issue":{"title":"ZX-B-OWNED-CONTENT","description":"owned by user 230","status":"Open"}})
print(f"  {c} {b[:300].replace(chr(10),' ')}")
if c in ('200','201'):
    try:
        i=json.loads(b)['issues'][0]
        print(f"  created id={i['id']} title={i.get('title')!r} creator={i.get('creator_user_id')} owner={i.get('owner_id')}")
        open('/tmp/b_issue','w').write(str(i['id']))
    except Exception as e: print("  parse",e)
print()
print("=== B(230) creates a narrative ===")
c,b=req('POST','/api/v1/narratives',{"narrative":{"title":"ZX-B-NARRATIVE","body":"owned by 230"}})
print(f"  {c} {b[:300].replace(chr(10),' ')}")
if c in ('200','201'):
    try:
        n=json.loads(b)['narratives'][0]
        print(f"  created id={n['id']} title={n.get('title')!r}")
        open('/tmp/b_narr','w').write(str(n['id']))
    except Exception as e: print("  parse",e)
