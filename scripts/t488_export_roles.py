import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-AuditBoard-Source: SchemaTable Rows','-H','Accept: text/csv, application/msexcel']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
cols=[{"path":"id","label":"ID"},{"path":"email","label":"Email"},{"path":"fullName","label":"Name"}]
print("=== export by role: users table (contains all 354 users + emails) ===")
for r in ['OWNER','SYSADMIN','TESTER','TPU']:
    tok=open(f'/tmp/bac_{r}').read().strip()
    body={"exportColumns":cols,"query":{},"format":"csv","timezone":"UTC","fileName":"zx"}
    c,b=req('POST','/api/v1/users/export',body,tok=tok)
    print(f"  {r:9} users/export -> {c} {b[:100].replace(chr(10),' ')}")
print()
print("=== async variant by role ===")
for r in ['OWNER','TESTER','TPU']:
    tok=open(f'/tmp/bac_{r}').read().strip()
    body={"exportColumns":cols,"query":{},"format":"csv","timezone":"UTC","fileName":"zx"}
    c,b=req('POST','/api/v1/users/_op/async_export',body,tok=tok)
    print(f"  {r:9} async_export -> {c} {b[:110].replace(chr(10),' ')}")
