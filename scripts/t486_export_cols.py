import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TO=open('/tmp/bac_OWNER').read().strip()
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-AuditBoard-Source: SchemaTable Rows','-H','Accept: text/csv, application/msexcel']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== crack exportColumns object shape ===")
shapes=[
 [{"key":"id"}],
 [{"name":"id"}],
 [{"field":"id"}],
 [{"path":"id"}],
 [{"key":"id","label":"ID"}],
 [{"name":"id","label":"ID","type":"string"}],
]
for cols in shapes:
    body={"exportColumns":cols,"query":{},"format":"csv","timezone":"UTC","fileName":"zx"}
    c,b=req('POST','/api/v1/users/_op/async_export',body,tok=TO)
    print(f"  {json.dumps(cols)[:60]:62} -> {c} {b[:120].replace(chr(10),' ')}")
