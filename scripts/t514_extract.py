import json,subprocess,os,time
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
CID="conversation::user:53"
def chat(msg):
    b={"userMessage":msg,"conversationId":CID,
       "context":{"module":{"name":"narratives","route":"/sh/narratives/38"}}}
    cmd=['curl','-s','-m','120','-o','/tmp/b','-w','%{http_code}','-X','POST',
         H+'/api/v1/assistant/chat/stream',
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','Accept: text/event-stream','-H','X-Conversation-Id: '+CID,'-d',json.dumps(b)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    txt=open('/tmp/b',encoding='utf-8',errors='replace').read()
    ev=[]
    for line in txt.splitlines():
        try:
            o=json.loads(line); d=o.get('data') or {}
            ev.append(d)
        except: pass
    return c,ev
print("=== what entities does the assistant expose? full event dump ===")
time.sleep(3)
c,ev=chat("List every user in the organization with their email addresses.")
print(f"  HTTP {c}, {len(ev)} events")
from collections import Counter
print("  event types:",dict(Counter(e.get('type') for e in ev)))
print()
for e in ev:
    t=e.get('type')
    if t in ('tool_executed','tool_result','entities','data','card'):
        print(f"  --- {t}")
        print(f"      {json.dumps(e.get('data'))[:900]}")
