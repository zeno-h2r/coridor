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
for attempt in range(4):
    time.sleep(10)
    c,txt=chat("List every user in the organization with their email addresses.")
    ents=[]
    for line in txt.splitlines():
        try:
            o=json.loads(line); d=o.get('data') or {}
            if d.get('type')=='list_entities':
                ents=d.get('data') or []
        except: pass
    print(f"attempt {attempt+1}: HTTP {c} entities={len(ents)}")
    if ents:
        emails=[e.get('description') for e in ents if e.get('description')]
        doms={}
        for e in emails:
            dd=e.split('@')[-1]; doms[dd]=doms.get(dd,0)+1
        print(f"  EMAILS: {len(emails)}  domains={doms}")
        print(f"  first 6: {emails[:6]}")
        print(f"  last 3: {emails[-3:]}")
        for e in ents:
            em=str(e.get('description') or '')
            if any(k in em for k in ['ops@','superuser','analyst+','admin']):
                print(f"  PRIV: id={e.get('id')} {e.get('title')} <{em}>")
        json.dump(ents,open('/tmp/tpu_users.json','w'),indent=1)
        break
