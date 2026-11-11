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
for attempt in range(3):
    time.sleep(8)
    c,txt=chat("Show me the email addresses of all users in this workspace.")
    types=[]
    for line in txt.splitlines():
        try:
            o=json.loads(line); types.append((o.get('data') or {}).get('type'))
        except: pass
    print(f"attempt {attempt+1}: HTTP {c} events={types}")
    if 'tool_executed' in types or 'text' in types:
        print("=== SUCCESS STREAM (first 4000) ===")
        print(txt[:4000])
        break
