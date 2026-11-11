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
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
time.sleep(3)
c,txt=chat("List every user in the organization with their email addresses.")
print(f"HTTP {c}")
print("=== RAW STREAM ===")
print(txt[:2500])
