import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
def post(p,body):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X','POST',H+p,
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-AuditBoard-Source: SchemaTable Rows','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== find a TaskItem / OpsAuditItem / QuestionResponse to comment on ===")
for ent in ['task_item','ops_audit_item','question_response','issue','risk','control']:
    c,b=post(f'/api/v1/table/query?entities={ent}',
             {"ab:query":{"entities":[ent],"filter":{},"include":[ent]}})
    ids=[]
    try: ids=[i['id'] for i in (json.loads(b).get('included') or [])][:5]
    except: pass
    print(f"  {ent:20} {c} ids={ids}")
