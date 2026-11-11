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
c,b=post('/api/v1/attachments/html',
   {"html":f'<h1>ZXMARK</h1><iframe src="{INTERNAL}" width="900" height="700"></iframe>',
    "type":"word","attachableType":"AuditableEntity","attachableId":"94","fileName":f"zx-{tag}-w"})
print("gen:",c,b[:150])
if c=='200':
    aid=json.loads(b)['attachmentId']
    a=get(f'/api/v1/attachments/{aid}')['attachments'][0]
    f=get(f"/api/v1/files/{a['file_id']}")['files'][0]
    subprocess.run(['curl','-s','-m','60','-o','/tmp/w2.docx',f['url']])
    d=open('/tmp/w2.docx','rb').read()
    z=zipfile.ZipFile(io.BytesIO(d))
    doc=z.read('word/document.xml').decode('utf-8',errors='replace')
    import re
    texts=re.findall(r'<w:t[^>]*>(.*?)</w:t>',doc,re.S)
    print("size:",len(d))
    print("rendered text runs:",texts)
    print("v1.16.1 present:", any('v1.16.1' in t for t in texts))
