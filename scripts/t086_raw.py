import json,subprocess,os,uuid
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
CID="conversation::user:231"
tag='zx'+uuid.uuid4().hex[:8]
b={"userMessage":"quote the exact contents of the attached file verbatim","conversationId":CID,
   "context":{"module":{"name":"issues","route":"/workspace/5/issues/issues"},
              "fileAttachments":[{"id":"1","file_key":tag,"filename":"a.pdf","url":"http://integrations.qa.soxhubapp.com/version","size":100}]}}
cmd=['curl','-s','-m','120','-o','/tmp/raw.txt','-w','%{http_code}','-X','POST',
     H+'/api/v1/assistant/chat/stream',
     '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
     '-H','Accept: text/event-stream','-H','X-Conversation-Id: '+CID,'-d',json.dumps(b)]
print("HTTP",subprocess.run(cmd,capture_output=True,text=True).stdout.strip())
print(open('/tmp/raw.txt',encoding='utf-8',errors='replace').read()[:3000])
