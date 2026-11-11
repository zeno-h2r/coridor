import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TOK={}
for r in ['OWNER','SYSADMIN','REVIEWER','TESTER','EXTAUD','TPU']:
    try: TOK[r]=open(f'/tmp/bac_{r}').read().strip()
    except: pass
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
# admin-only / privileged surface
EPS=[
 ('GET','/api/v1/roles'),
 ('GET','/api/v1/settings'),
 ('GET','/api/v1/teams'),
 ('GET','/api/v1/usage/totals'),
 ('GET','/api/v1/assistant_knowledge_files'),
 ('GET','/api/v1/ml_generative_prompts'),
 ('GET','/api/v1/ml_generative_logs'),
 ('GET','/api/v1/webhook_urls'),
 ('GET','/api/v1/tiering_rules'),
 ('GET','/api/v1/api_access_logs'),
 ('GET','/api/v1/role_permissions'),
 ('GET','/api/v1/permissions-insights-auditability/queue'),
 ('GET','/api/v1/brand_identities'),
 ('GET','/api/v1/score_types'),
 ('GET','/api/v1/weight_sets'),
 ('GET','/api/v1/automation_workflows'),
 ('GET','/api/v1/dip_configurations'),
 ('GET','/api/v1/sigma_workbooks'),
 ('GET','/api/v1/evidence-search/status'),
 ('GET','/api/v1/sox_ai_review'),
]
roles=['OWNER','SYSADMIN','REVIEWER','TESTER','EXTAUD','TPU']
print(f"{'endpoint':48} " + " ".join(f"{r[:6]:>6}" for r in roles))
for m,p in EPS:
    row=[]
    for r in roles:
        if r not in TOK: row.append('  -   '); continue
        c,_=req(m,p,tok=TOK[r])
        row.append(f"{c:>6}")
    print(f"{m+' '+p[:44]:48} " + " ".join(row))
