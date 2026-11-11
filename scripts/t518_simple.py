import json,subprocess,os,time
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
CID="conversation::user:53"
def chat(msg):
    b={"userMessage":msg,"conversationId":CID,
       "context":{"module":{"name":"narratives","route":"/sh/narratives/38"}}}
    cmd=['curl','-s','-m','150','-o','/tmp/b','-w','%{http_code}','-X','POST',
         H+'/api/v1/assistant/chat/stream',
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','Accept: text/event-stream','-H','X-Conversation-Id: '+CID,'-d',json.dumps(b)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== is the assistant alive at all? ===")
for msg in ["hi","what is 2+2","hello"]:
    time.sleep(6)
    c,txt=chat(msg)
    types=[]
    for line in txt.splitlines():
        try:
            o=json.loads(line); types.append((o.get('data') or {}).get('type'))
        except: pass
    ok = 'text' in types
    print(f"  {msg:14} -> {c} events={types} {'OK' if ok else 'FAILED'}")
    if ok:
        # extract text
        out=[]
        for line in txt.splitlines():
            try:
                o=json.loads(line); d=o.get('data') or {}
                if d.get('type')=='text': out.append(d['data'].get('chunk',''))
            except: pass
        print(f"     answer: {''.join(out)[:200]!r}")
        break
