import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    code=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return code,open('/tmp/b',encoding='utf-8',errors='replace').read()
for ent in ['file','file_version','issue','user','document_version','attachment']:
    c,b=req('POST',f'/api/v1/table/count?entities={ent}',{"ab:query":{"entities":ent,"filter":{}}})
    print(f"count {ent}: {c} {b[:200]}")
    c,b=req('POST',f'/api/v1/table/ids?entities={ent}',{"ab:query":{"entities":ent,"filter":{}}})
    print(f"ids   {ent}: {c} {b[:200]}\n")
