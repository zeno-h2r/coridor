import json,subprocess,os,uuid
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
CID="conversation::user:231"
tag='zx'+uuid.uuid4().hex[:8]
b={"userMessage":"what is in this file?","conversationId":CID,
   "context":{"module":{"name":"issues","route":"/workspace/5/issues/issues"},
              "fileAttachments":[{"id":"1","file_key":tag,"filename":"e.md","url":"https://example.com","size":100}]}}
cmd=['curl','-s','-m','120','-o','/tmp/raw2.txt','-w','%{http_code}','-X','POST',
     H+'/api/v1/assistant/chat/stream',
     '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
     '-H','Accept: text/event-stream','-H','X-Conversation-Id: '+CID,'-d',json.dumps(b)]
print("HTTP",subprocess.run(cmd,capture_output=True,text=True).stdout.strip())
d=open('/tmp/raw2.txt',encoding='utf-8',errors='replace').read()
print("bytes:",len(d))
for line in d.splitlines():
    try:
        o=json.loads(line)
        t=o.get('type')
        if t!='text': print(t,'|',json.dumps(o.get('data'))[:300])
    except Exception as e: print("RAW:",line[:200])
