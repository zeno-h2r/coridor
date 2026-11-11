import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
def req(m,p,body=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='ZXA'+uuid.uuid4().hex[:5]
print("=== audit log: what does it store for a field change? ===")
# change a field with a benign-but-marked value, then read the audit log
c,b=req('PUT','/api/v1/exception_requests/33',{"exception_request":{"title":f'<b>ZXAUDIT{tag}</b>'}})
print(f"  PUT title -> {c}")
c,b=req('GET','/api/v1/exception_requests/33')
try:
    o=json.loads(b)['exception_requests'][0]
    print(f"  stored title={o.get('title')!r}")
except: pass
print()
print("=== audit log endpoints ===")
for p in ['/api/v1/exception_requests/33/audit_log','/api/v1/audit_logs?filter[auditable_id][eq]=33',
          '/api/v1/global_audits?filter[object_id][eq]=33','/api/v1/audit_logs']:
    c,b=req('GET',p)
    print(f"  {c} {p}  {b[:180].replace(chr(10),' ')}")
