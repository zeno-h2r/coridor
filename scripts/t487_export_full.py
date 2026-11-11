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
print("=== exportColumns with path+label ===")
cols=[{"path":"id","label":"ID"},{"path":"email","label":"Email"}]
for model in ['users','issues','controls']:
    body={"exportColumns":cols,"query":{},"format":"csv","timezone":"UTC","fileName":"zx"}
    c,b=req('POST',f'/api/v1/{model}/export',body,tok=TO)
    print(f"\n  {model}/export -> {c}")
    print(f"    {b[:300].replace(chr(10),' ')}")
    if c=='200':
        print(f"    *** CSV/EXCEL RETURNED, {len(b)} bytes ***")
        print(f"    head: {b[:200]!r}")
