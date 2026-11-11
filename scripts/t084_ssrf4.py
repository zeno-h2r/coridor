import json,subprocess,os,uuid
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']; WH=os.environ['WH']
CID="conversation::user:231"
def req(body):
    cmd=['curl','-s','-m','90','-o','/tmp/b','-w','%{http_code}','-X','POST',
         H+'/api/v1/assistant/chat/stream',
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','Accept: text/event-stream','-H','X-Conversation-Id: '+CID,'-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='zx'+uuid.uuid4().hex[:8]
url=f"{WH}/{tag}.pdf"
b={"userMessage":"summarize the attached file","conversationId":CID,
   "context":{"module":{"name":"issues","route":"/workspace/5/issues/issues"},
              "fileAttachments":[{"id":"1","file_key":tag+".pdf","filename":tag+".pdf","url":url,"size":100}]}}
c,txt=req(b)
print("with attach:",c,len(txt)); print(txt[:2500])
open('/tmp/tag','w').write(tag)
