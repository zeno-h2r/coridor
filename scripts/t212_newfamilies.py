import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-AuditBoard-Source: SchemaTable Rows']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
tests=[
 ('GET','/api/v1/processes/1',None),
 ('GET','/api/v1/ticketing/tickets',None),
 ('GET','/api/v1/ticketing/tickets/1',None),
 ('GET','/api/v1/ticketing/tickets/1/comments',None),
 ('GET','/api/v1/ticketing/users/1',None),
 ('GET','/api/v1/workflow_schema_runs/1',None),
 ('GET','/api/v1/workflow_schema_runs/1/completions',None),
 ('POST','/api/v1/entities/1/migrate/run',{}),
 ('POST','/api/v1/entities/92/migrate/run',{"dry_run":True}),
 ('GET','/api/v1/frameworks/content-service/frameworks',None),
 ('GET','/api/v1/library/preload',None),
 ('GET','/api/v1/library/attributes',None),
 ('GET','/api/v1/scores/latest?id=1',None),
 ('GET','/api/v1/auditable_entities/count?id=1',None),
 ('GET','/api/v1/auditable_entity_types/count?id=1',None),
 ('GET','/api/v1/threats/count?id=1',None),
 ('POST','/api/v1/table/_op/async_export?entities=user',
   {"ab:query":{"entities":["user"],"filter":{}},
    "ab:export":{"header":["email","fullName"],"format":"csv","timezone":"UTC","fileName":"zx-exp"}}),
]
for m,p,b in tests:
    c,t=req(m,p,b)
    mark='  <<<' if c in ('200','201','202') else ''
    print(f"  {c} {m:5} {p[:56]:58} {t[:110].replace(chr(10),' ')}{mark}")
