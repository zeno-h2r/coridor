import json,subprocess,os,time
H=os.environ['H']; BB=os.environ['BB']
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-AuditBoard-Source: SchemaTable Rows']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
TT=open('/tmp/bac_TPU').read().strip()
cols=[{"path":"id","label":"ID"},{"path":"email","label":"Email"}]
print("=== TPU queues a users export, then hunts for the artifact ===")
body={"exportColumns":cols,"query":{},"format":"csv","timezone":"UTC","fileName":"zx-tpu-export"}
c,b=req('POST','/api/v1/users/export',body,tok=TT)
print(f"  queue -> {c} {b[:120]}")
time.sleep(4)
print()
print("=== where does the export land? check files ===")
c,b=req('GET','/api/v1/files?page[size]=5',tok=TT)
print(f"  TPU GET /files -> {c} {b[:200].replace(chr(10),' ')}")
print()
print("=== table/query for export job records ===")
for ent in ['export','export_job','table_export','async_export']:
    c,b=req('POST',f'/api/v1/table/query?entities={ent}',
            {"ab:query":{"entities":[ent],"filter":{},"include":[ent]}},tok=TT)
    n=0
    try: n=len(json.loads(b).get('included') or [])
    except: pass
    print(f"  {c} entities={ent:14} rows={n} {b[:80].replace(chr(10),' ')}")
print()
print("=== TPU: can it read the export via /files or attachments? ===")
for p in ['/api/v1/attachments','/api/v1/files']:
    c,b=req('GET',p,tok=TT)
    print(f"  {c} {p} {b[:150].replace(chr(10),' ')}")
