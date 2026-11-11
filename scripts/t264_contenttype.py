import json,subprocess,os,uuid,zipfile,io
H=os.environ['H']; BB=os.environ['BB']; WH=os.environ['WH']
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
tests=[
 ("html-text","https://example.com"),
 ("json-api","https://httpbin.org/json"),
 ("plain-text","https://httpbin.org/robots.txt"),
 ("real-png","https://httpbin.org/image/png"),
 ("webhook-png",f"{WH}/{tag}-ct.png"),
]
for label,url in tests:
    c,b=post('/api/v1/attachments/html',
       {"html":f'<h1>ZX</h1><img src="{url}" width="800" height="600">',
        "type":"word","attachableType":"AuditableEntity","attachableId":"102",
        "fileName":f"zx-{tag}-{label}"})
    if c!='200':
        print(f"  {label:14} gen={c} {b[:80].replace(chr(10),' ')}"); continue
    aid=json.loads(b)['attachmentId']
    a=get(f'/api/v1/attachments/{aid}')['attachments'][0]
    f=get(f"/api/v1/files/{a['file_id']}")['files'][0]
    subprocess.run(['curl','-s','-m','60','-o','/tmp/c.docx',f['url']])
    d=open('/tmp/c.docx','rb').read()
    try:
        z=zipfile.ZipFile(io.BytesIO(d))
        media=[(n,len(z.read(n))) for n in z.namelist() if 'media' in n]
        print(f"  {label:14} docx={len(d):>6}B media={media}")
        for m,_ in media:
            print(f"      head={z.read(m)[:60]!r}")
    except Exception as e:
        print(f"  {label:14} not zip {e}")
