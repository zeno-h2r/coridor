import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TB=open('/tmp/tok_B-230').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or TB),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
# get valid issue category/type options
c,b=req('GET','/api/v1/library/preload')
cats=[]
try:
    d=json.loads(b)
    for i in d.get('included') or []:
        if i.get('type') in ('issue-category','issue-ident','issue-rating'):
            a=i.get('attributes') or {}
            cats.append((i.get('type'),i.get('id'),a.get('name')))
except Exception as e: print("preload err",e)
print("issue option sets:",cats[:8])
print()
# narrative: needs title + uid
c,b=req('POST','/api/v1/narratives',{"narrative":{"title":"ZX-B-NARRATIVE","uid":"zx-b-narr-1","body":"owned by 230"}})
print(f"narrative -> {c} {b[:350].replace(chr(10),' ')}")
if c in ('200','201'):
    try:
        n=json.loads(b)['narratives'][0]
        print(f"  created id={n['id']} title={n.get('title')!r} creator={n.get('creator_user_id')}")
        open('/tmp/b_narr','w').write(str(n['id']))
    except Exception as e: print("  parse",e)
