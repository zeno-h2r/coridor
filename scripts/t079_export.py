import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def post(path,body):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-AuditBoard-Source: SchemaTable Rows','-d',json.dumps(body)]
    code=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return code,open('/tmp/b',encoding='utf-8',errors='replace').read()
def body(ent,fmt='csv',hdr=None):
    return {"ab:query":{"entities":[ent],"filter":{}},
            "ab:export":{"header":hdr or [],"format":fmt,"timezone":"UTC","fileName":"zx-"+ent}}
for ent,fmt in [('user','csv'),('file','csv'),('issue','csv')]:
    c,b=post(f'/api/v1/table/export?entities={ent}',body(ent,fmt))
    print(f"--- export {ent} {fmt}: {c} len={len(b)}")
    print(b[:400].replace(chr(10),' '))
    print()
