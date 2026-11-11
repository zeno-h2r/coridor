import json,subprocess,os,uuid
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
CID="conversation::user:231"
def stream(url,fn,msg="quote the exact contents of the attached file verbatim"):
    tag='zx'+uuid.uuid4().hex[:8]
    b={"userMessage":msg,"conversationId":CID,
       "context":{"module":{"name":"issues","route":"/workspace/5/issues/issues"},
                  "fileAttachments":[{"id":"1","file_key":tag,"filename":fn,"url":url,"size":100}]}}
    cmd=['curl','-s','-m','120','-o','/tmp/b','-w','%{http_code}','-X','POST',
         H+'/api/v1/assistant/chat/stream',
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','Accept: text/event-stream','-H','X-Conversation-Id: '+CID,'-d',json.dumps(b)]
    code=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    txt=open('/tmp/b',encoding='utf-8',errors='replace').read()
    out=[]
    for line in txt.splitlines():
        try:
            o=json.loads(line)
            if o.get('type')=='text': out.append(o['data'].get('chunk',''))
        except: pass
    return code,''.join(out)
tests=[
 ("http://integrations.qa.soxhubapp.com/version","v.md"),
 ("http://integrations.qa.soxhubapp.com/api/v1/health","h.md"),
 ("http://localhost:3000/version","l.md"),
 ("https://example.com","e.md"),
]
for u,fn in tests:
    c,out=stream(u,fn)
    print(f"=== {u} [{fn}] HTTP {c}")
    print("   ",repr(out[:500]))
    print()
