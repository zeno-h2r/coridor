import json,subprocess,os,time
H=os.environ['H']; BB=os.environ['BB']
TP=open('/tmp/bac_TPU').read().strip()
CID="conversation::user:315"
def chat(msg):
    b={"userMessage":msg,"conversationId":CID,
       "context":{"module":{"name":"narratives","route":"/sh/narratives/38"}}}
    cmd=['curl','-s','-m','150','-o','/tmp/b','-w','%{http_code}','-X','POST',
         H+'/api/v1/assistant/chat/stream',
         '-H','token: '+TP,'-H',BB,'-H','Content-Type: application/json',
         '-H','Accept: text/event-stream','-H','X-Conversation-Id: '+CID,'-d',json.dumps(b)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
time.sleep(4)
c,txt=chat("List every user in the organization with their email addresses.")
print(f"HTTP {c}  stream bytes={len(txt)}")
print()
from collections import Counter
types=[]
for line in txt.splitlines():
    try:
        o=json.loads(line); d=o.get('data') or {}
        types.append(d.get('type'))
    except: pass
print("event type counts:",dict(Counter(types)))
print()
# dump every non-text event fully
for line in txt.splitlines():
    try:
        o=json.loads(line); d=o.get('data') or {}
        t=d.get('type')
        if t in ('list_entities','entities','cards','data','entity_list'):
            print(f"=== {t} ===")
            print(json.dumps(d.get('data'))[:2500])
            print()
    except: pass
