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
print(f"HTTP {c}")
print()
print("=== tool calls ===")
for line in txt.splitlines():
    try:
        o=json.loads(line); d=o.get('data') or {}
        if d.get('type')=='tool_executed':
            dd=d['data']
            print(f"  {dd.get('tool_name'):22} status={dd.get('status')} metadata={json.dumps(dd.get('metadata'))[:120]}")
    except: pass
print()
print("=== assistant text answer ===")
out=[]
for line in txt.splitlines():
    try:
        o=json.loads(line); d=o.get('data') or {}
        if d.get('type')=='text': out.append(d['data'].get('chunk',''))
    except: pass
ans=''.join(out)
print(ans[:1500])
print()
print(f"=== answer length: {len(ans)} chars ===")
import re
emails=re.findall(r'[\w\.\-+]+@[\w\.\-]+\.\w+', ans)
print(f"=== emails found in answer: {len(emails)} ===")
for e in emails[:15]: print("  ",e)
open('/tmp/tpu_answer.txt','w').write(ans)
