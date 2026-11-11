import json,subprocess,os,uuid,zipfile,io,re
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
# public PNG that definitely exists
IMG='https://httpbin.org/image/png'
print("=== does the DOCX embed a fetched external image? ===")
c,b=post('/api/v1/attachments/html',
   {"html":f'<h1>ZX</h1><img src="{IMG}" width="200" height="200">',
    "type":"word","attachableType":"AuditableEntity","attachableId":"100",
    "fileName":f"zx-{tag}-embed"})
print(f"  gen -> {c} {b[:130].replace(chr(10),' ')}")
if c=='200':
    aid=json.loads(b)['attachmentId']
    a=get(f'/api/v1/attachments/{aid}')['attachments'][0]
    f=get(f"/api/v1/files/{a['file_id']}")['files'][0]
    subprocess.run(['curl','-s','-m','60','-o','/tmp/e.docx',f['url']])
    d=open('/tmp/e.docx','rb').read()
    try:
        z=zipfile.ZipFile(io.BytesIO(d))
        names=z.namelist()
        media=[n for n in names if n.startswith('word/media')]
        print(f"  docx={len(d)}B entries={len(names)}")
        print(f"  media entries: {media}")
        if media:
            for m in media:
                print(f"    {m}: {len(z.read(m))} bytes")
        doc=z.read('word/document.xml').decode('utf-8',errors='replace')
        print(f"  document.xml has drawing: {'drawing' in doc}")
        print(f"  document.xml has blip: {'blip' in doc}")
    except Exception as e:
        print("  not zip:",e,d[:100])
