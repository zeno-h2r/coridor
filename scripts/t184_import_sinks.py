import json,subprocess,os,uuid
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']; WH=os.environ['WH']
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','45','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or T),'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='zx'+uuid.uuid4().hex[:8]
U=f"{WH}/{tag}-imp"
print("=== server-side fetch sinks (URL supplied by caller) ===")
tests=[
 ('POST','/api/v1/regulations/import',{"url":U}),
 ('POST','/api/v1/regulations/sync',{"url":U}),
 ('POST','/api/v1/regulations/sync_ontologies',{"url":U}),
 ('POST','/api/v1/regulatory-signals/sync',{"url":U}),
 ('POST','/api/v1/regulatory-signals/sync_ontologies',{"url":U}),
 ('POST','/api/v1/frameworks/custom-import',{"url":U}),
 ('POST','/api/v1/import_tools/upload',{"url":U}),
 ('POST','/api/v1/import_tools/validate',{"url":U}),
 ('POST','/api/v1/bcm_plans/import',{"url":U}),
 ('POST','/api/v1/ops_audit_items/import/json',{"url":U}),
 ('POST','/api/v1/vms/csv-import',{"url":U}),
 ('POST','/api/v1/sigma/sync_workbooks',{"url":U}),
 ('POST','/api/v1/lucidcharts/link',{"url":U}),
 ('POST','/api/v1/lucidcharts/import_into/1',{"url":U}),
 ('POST','/api/v1/field_mappings/validate',{"url":U}),
 ('POST','/api/v1/ticketing/ticket_by_url',{"url":U}),
 ('POST','/api/v1/ml-recommendations/files/generate_sample_file',{"url":U}),
 ('POST','/api/v1/regulatory-profiles/autofill',{"url":U}),
]
for m,p,b in tests:
    c,t=req(m,p,b)
    mark='  <<<' if c in ('200','201','202') else ''
    print(f"  {c} {p:52} {t[:110].replace(chr(10),' ')}{mark}")
open('/tmp/tag184','w').write(tag)
