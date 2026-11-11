import json,subprocess,os,uuid,re,zlib
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
def post(path,body):
    cmd=['curl','-s','-m','90','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
def get(p):
    cmd=['curl','-s','-m','30',H+p,'-H','token: '+TOK,'-H',BB]
    return json.loads(subprocess.run(cmd,capture_output=True,text=True).stdout)
tag='ZXD'+uuid.uuid4().hex[:5]
print("=== renderer: does it decode stored entities into live markup? ===")
# entities that would become a real tag if decoded once
html=f'<p>&amp;lt;img src=x onerror=alert(1)&amp;gt;{tag}</p>'
c,b=post('/api/v1/attachments/html',
   {"html":html,"type":"word","attachableType":"AuditableEntity",
    "attachableId":"120","fileName":f"zx-{tag}"})
print(f"  gen -> {c} {b[:120].replace(chr(10),' ')}")
if c=='200':
    aid=json.loads(b)['attachmentId']
    a=get(f'/api/v1/attachments/{aid}')['attachments'][0]
    f=get(f"/api/v1/files/{a['file_id']}")['files'][0]
    subprocess.run(['curl','-s','-m','60','-o','/tmp/dec.docx',f['url']])
    import zipfile,io
    d=open('/tmp/dec.docx','rb').read()
    z=zipfile.ZipFile(io.BytesIO(d))
    doc=z.read('word/document.xml').decode('utf-8',errors='replace')
    runs=re.findall(r'<w:t[^>]*>(.*?)</w:t>',doc,re.S)
    print(f"  rendered runs: {runs}")
    print(f"  contains literal '&lt;img': {'&lt;img' in doc}")
    print(f"  contains decoded '<img': {'<img' in doc}")
