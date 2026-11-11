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
print("=== per-model export path (exportColumns shape) ===")
for model in ['users','issues','controls','risks','timesheet_entries']:
    body={"exportColumns":["id","email"],"query":{},"format":"csv","timezone":"UTC","fileName":"zx"}
    c,b=req('POST',f'/api/v1/{model}/export',body,tok=TO)
    print(f"  {c} /api/v1/{model}/export  {b[:140].replace(chr(10),' ')}")
print()
print("=== async variant ===")
for model in ['users','issues']:
    for body in [{"ab:query":{"entities":[model],"filter":{}},"ab:export":{"header":["id"],"format":"csv","timezone":"UTC","fileName":"zx"}},
                 {"exportColumns":["id"],"query":{},"format":"csv","timezone":"UTC","fileName":"zx"}]:
        c,b=req('POST',f'/api/v1/{model}/_op/async_export',body,tok=TO)
        print(f"  {c} /api/v1/{model}/_op/async_export  {b[:120].replace(chr(10),' ')}")
