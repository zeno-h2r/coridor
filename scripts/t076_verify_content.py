import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()

c,b=req('GET','/api/v1/files/2692')
print("GET /files/2692 ->",c)
try:
    d=json.loads(b); f=d['files'][0]
    print("  name:",f.get('name'),"size:",f.get('size'))
    print("  key:",f.get('key'))
    print("  meta:",json.dumps(f.get('meta')))
    url=f.get('url')
    print("  url prefix:",url[:130])
    open('/tmp/url2692','w').write(url)
except Exception as e:
    print("parse err",e,b[:400])
