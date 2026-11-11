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
print("=== correct operator syntax (from bundle: {field:{op:val}}) ===")
probes=[
 ("baseline-noop", {}),
 ("$in", {"email":{"$in":["0707@soxhub.com"]}}),
 ("$contains", {"email":{"$contains":"soxhub"}}),
 ("$eq", {"email":{"$eq":"0707@soxhub.com"}}),
 ("$ne-array", {"email":{"$ne":["x"]}}),
 ("$ne-string", {"email":{"$ne":"x"}}),
 ("$like", {"email":{"$like":"%soxhub%"}}),
 ("$nin", {"email":{"$nin":["x"]}}),
]
for label,f in probes:
    t0=time.time()
    c,b=post({"ab:query":{"entities":["user"],"filter":f,"include":["user"]}})
    dt=round(time.time()-t0,2)
    n=0
    try: n=len(json.loads(b).get('included') or [])
    except: pass
    print(f"  {label:16} {c:>4} rows={n:<5} t={dt}s  {b[:80].replace(chr(10),' ')}")
