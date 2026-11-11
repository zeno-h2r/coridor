import json,subprocess,os,time,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
def req(m,p,body=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== create a FRESH conversation (old one may be poisoned) ===")
c,b=req('POST','/api/v1/assistant/conversations',{"conversationId":None})
print(f"  create -> {c} {b[:200]}")
cid=None
try: cid=json.loads(b)['data']['id']
except: pass
if not cid: cid=f"conversation::user:53"
print(f"  using cid={cid}")
def chat(msg,conv):
    body={"userMessage":msg,"conversationId":conv,
          "context":{"module":{"name":"narratives","route":"/sh/narratives/38"}}}
    cmd=['curl','-s','-m','150','-o','/tmp/b','-w','%{http_code}','-X','POST',
         H+'/api/v1/assistant/chat/stream',
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','Accept: text/event-stream','-H','X-Conversation-Id: '+conv,'-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
time.sleep(5)
c,txt=chat("List every user in the organization with their email addresses.",cid)
types=[]
for line in txt.splitlines():
    try:
        o=json.loads(line); types.append((o.get('data') or {}).get('type'))
    except: pass
print(f"  chat -> {c} events={types}")
if 'text' in types:
    print("=== SUCCESS ===")
    print(txt[:3000])
else:
    print(txt[:600])
