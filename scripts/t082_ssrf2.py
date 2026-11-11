import json,subprocess,os,uuid
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']; WH=os.environ['WH']
CID="conversation::user:231"
def req(path,body,extra=None):
    cmd=['curl','-s','-m','90','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','Accept: text/event-stream','-H','X-Conversation-Id: '+CID]
    if extra:
        for k,v in extra.items(): cmd+=['-H',f'{k}: {v}']
    cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='zx'+uuid.uuid4().hex[:8]
url=f"{WH}/{tag}.pdf"
body={"message":"summarize the attached file","conversationId":CID,
      "context":{"fileAttachments":[{"id":"1","file_key":tag+".pdf","filename":tag+".pdf","url":url,"size":100}]}}
c,b=req('/api/v1/assistant/chat/stream',body)
print("stream:",c,"len",len(b))
print(b[:2000])
open('/tmp/tag','w').write(tag)
