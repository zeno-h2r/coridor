import json,subprocess,os,uuid
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']; WH=os.environ['WH']
def req(method,path,body=None):
    cmd=['curl','-s','-m','90','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='zx'+uuid.uuid4().hex[:8]
url=f"{WH}/{tag}.pdf"
body={"message":"read this file","context":{"fileAttachments":[
  {"id":"1","file_key":tag+".pdf","filename":tag+".pdf","url":url,"size":100}]}}
c,b=req('POST','/api/v1/assistant/conversations/chat',body)
print("chat:",c)
print(b[:1500])
open('/tmp/tag','w').write(tag)
