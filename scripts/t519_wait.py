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
print("=== polling assistant recovery (60s intervals) ===")
for i in range(4):
    time.sleep(60)
    c,txt=chat("hi")
    types=[]
    for line in txt.splitlines():
        try:
            o=json.loads(line); types.append((o.get('data') or {}).get('type'))
        except: pass
    ok='text' in types
    print(f"  poll {i+1}: {c} events={types} {'RECOVERED' if ok else 'still down'}")
    if ok: break
