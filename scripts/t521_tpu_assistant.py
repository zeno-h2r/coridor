import json,subprocess,os,time
H=os.environ['H']; BB=os.environ['BB']
TP=open('/tmp/bac_TPU').read().strip()
CID="conversation::user:315"
def chat(msg,tok,cid):
    b={"userMessage":msg,"conversationId":cid,
       "context":{"module":{"name":"narratives","route":"/sh/narratives/38"}}}
    cmd=['curl','-s','-m','150','-o','/tmp/b','-w','%{http_code}','-X','POST',
         H+'/api/v1/assistant/chat/stream',
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','Accept: text/event-stream','-H','X-Conversation-Id: '+cid,'-d',json.dumps(b)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== TPU (role 11, limited) vs assistant ===")
time.sleep(5)
c,txt=chat("List every user in the organization with their email addresses.",TP,CID)
types=[]
for line in txt.splitlines():
    try:
        o=json.loads(line); types.append((o.get('data') or {}).get('type'))
    except: pass
print(f"  chat -> {c} events={types}")
print(txt[:800])
print()
print("=== control: TPU direct API access ===")
def get(p):
    cmd=['curl','-s','-m','25','-o','/tmp/b','-w','%{http_code}',H+p,'-H','token: '+TP,'-H',BB]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
for p in ['/api/v1/users','/api/v1/users/1','/api/v1/narratives/38']:
    c,b=get(p)
    print(f"  {c} {p}  {b[:90].replace(chr(10),' ')}")
