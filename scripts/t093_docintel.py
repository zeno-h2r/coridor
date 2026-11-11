import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
# server-side readers against the foreign-copied file 2692
tests=[
 ('POST','/api/v1/document_intelligence/attachment',{"file_id":2692}),
 ('POST','/api/v1/document_intelligence/attachment',{"fileId":2692}),
 ('POST','/api/v1/document_intelligence/attachment',{"attachment_id":2692}),
 ('GET','/api/v1/document_intelligence/export/2692',None),
 ('POST','/api/v1/document_intelligence/export/pdf',{"file_id":2692}),
]
for m,p,b in tests:
    c,txt=req(m,p,b)
    print(f"{c} {m} {p} {json.dumps(b) if b else ''}")
    print("   ",txt[:300].replace(chr(10),' '))
