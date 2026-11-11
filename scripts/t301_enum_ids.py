import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
T=open('/tmp/bac_OWNER').read().strip()
def post(path,body):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-AuditBoard-Source: SchemaTable Rows','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
ENTS=['issue','control','risk','narrative','auditable_entity','policy','test',
      'ops_audit_item','esg_metric','exception_request','vendor','controls_datum',
      'framework_item','assessment','audit_survey']
found={}
for e in ENTS:
    c,b=post(f'/api/v1/table/query?entities={e}',
             {"ab:query":{"entities":[e],"filter":{},"include":[e]}})
    ids=[]
    try:
        inc=json.loads(b).get('included') or []
        ids=[i['id'] for i in inc][:3]
    except: pass
    found[e]=(c,ids)
    print(f"  {e:22} {c}  ids={ids}")
json.dump(found,open('state/edit_ids.json','w'),indent=1)
