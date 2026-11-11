import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
R2=open('/tmp/r2_301').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or T),'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
eps=[
 ('GET','/api/v1/settings',None),('GET','/api/v1/roles',None),('GET','/api/v1/teams',None),
 ('GET','/api/v1/usage/totals',None),('GET','/api/v1/usage/top-users',None),
 ('GET','/api/v1/webhook_urls',None),('GET','/api/v1/tiering_rules',None),
 ('GET','/api/v1/assistant_knowledge_files',None),('GET','/api/v1/ml_generative_prompts',None),
 ('GET','/api/v1/ml_generative_logs',None),('GET','/api/v1/ml_traces',None),
 ('GET','/api/v1/imported_third_parties',None),('GET','/api/v1/threats',None),
 ('GET','/api/v1/regulatory-signals/scoring-status',None),('GET','/api/v1/sigma/health_check',None),
 ('GET','/api/v1/sigma_workbooks',None),('GET','/api/v1/sigma_reports',None),
 ('GET','/api/v1/evidence-search/status',None),('GET','/api/v1/sox_ai_review',None),
 ('GET','/api/v1/dip_configurations',None),('GET','/api/v1/api_access_logs',None),
 ('GET','/api/v1/permissions-insights-auditability/queue',None),
 ('GET','/api/v1/role_permissions',None),('GET','/api/v1/global_permissions',None),
 ('GET','/api/v1/brand_identities',None),('GET','/api/v1/score_types',None),
 ('GET','/api/v1/weight_sets',None),('GET','/api/v1/automation_workflows',None),
]
print(f"{'endpoint':52} {'Owner':>6} {'SysAdm':>7}")
diffs=[]
for m,p,b in eps:
    c1,t1=req(m,p,b,tok=T)
    c2,t2=req(m,p,b,tok=R2)
    if c1!=c2:
        diffs.append((m,p,c1,c2,len(t2)))
        print(f"{m+' '+p[:46]:52} {c1:>6} {c2:>7}  <<< DIFF len={len(t2)}")
print(f"\ndifferentials: {len(diffs)}")
json.dump(diffs,open('state/t173_diffs.json','w'),indent=1)
