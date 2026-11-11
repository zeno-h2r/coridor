import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
for m,p,b in [
  ('GET','/api/v1/attachments/html',None),
  ('POST','/api/v1/attachments/html',{}),
  ('POST','/api/v1/attachments/html',{"html":"<h1>zx</h1>"}),
  ('POST','/api/v1/attachments/html',{"url":"https://example.com"}),
]:
    c,txt=req(m,p,b)
    print(f"{c} {m} {p} {json.dumps(b) if b else ''}")
    print("   ",txt[:400].replace(chr(10),' '))
