import json,subprocess,os,uuid,time
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
CID="conversation::user:231"
def chat(msg,attach=None):
    b={"userMessage":msg,"conversationId":CID,
       "context":{"module":{"name":"issues","route":"/workspace/5/issues/issues"}}}
    if attach: b["context"]["fileAttachments"]=attach
    cmd=['curl','-s','-m','120','-o','/tmp/b','-w','%{http_code}','-X','POST',
         H+'/api/v1/assistant/chat/stream',
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','Accept: text/event-stream','-H','X-Conversation-Id: '+CID,'-d',json.dumps(b)]
    code=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    txt=open('/tmp/b',encoding='utf-8',errors='replace').read()
    out=[];tools=[]
    for line in txt.splitlines():
        try:
            o=json.loads(line); d=o.get('data') or {}
            if d.get('type')=='text': out.append(d['data'].get('chunk',''))
            elif d.get('type')=='tool_executed': tools.append(d['data'].get('tool_name'))
        except: pass
    return code,''.join(out),tools
tag='zx'+uuid.uuid4().hex[:8]
att=[{"id":"1","file_key":tag,"filename":"zx.md","url":"https://example.com","size":100}]
c,o,t=chat("summarize the attached file",att)
print("1st:",c,t,repr(o[:300]))
print("waiting 45s for async indexing...")
time.sleep(45)
c,o,t=chat("what does the attached document say? list its headings")
print("2nd:",c,t,repr(o[:600]))
