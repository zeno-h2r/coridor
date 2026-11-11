import json,subprocess,os,sys
from concurrent.futures import ThreadPoolExecutor
H=os.environ['H']; BB=os.environ['BB']
TOK={}
for r in ['OWNER','SYSADMIN','REVIEWER','TESTER','EXTAUD','TPU']:
    try: TOK[r]=open(f'/tmp/bac_{r}').read().strip()
    except: pass
def one(args):
    r,m,p=args
    cmd=['curl','-s','-m','15','-o','/dev/null','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+TOK[r],'-H',BB,'-H','X-Auditboard-Product: System']
    try: return r,p,subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    except: return r,p,'ERR'
EPS=[('GET','/api/v1/roles'),('GET','/api/v1/settings'),('GET','/api/v1/teams'),
 ('GET','/api/v1/usage/totals'),('GET','/api/v1/assistant_knowledge_files'),
 ('GET','/api/v1/ml_generative_prompts'),('GET','/api/v1/ml_generative_logs'),
 ('GET','/api/v1/webhook_urls'),('GET','/api/v1/tiering_rules'),
 ('GET','/api/v1/api_access_logs'),('GET','/api/v1/role_permissions'),
 ('GET','/api/v1/permissions-insights-auditability/queue'),('GET','/api/v1/brand_identities'),
 ('GET','/api/v1/score_types'),('GET','/api/v1/weight_sets'),('GET','/api/v1/automation_workflows'),
 ('GET','/api/v1/dip_configurations'),('GET','/api/v1/sigma_workbooks'),
 ('GET','/api/v1/evidence-search/status'),('GET','/api/v1/sox_ai_review')]
roles=['OWNER','SYSADMIN','REVIEWER','TESTER','EXTAUD','TPU']
jobs=[(r,m,p) for m,p in EPS for r in roles if r in TOK]
res={}
with ThreadPoolExecutor(max_workers=12) as ex:
    for r,p,c in ex.map(one,jobs): res[(r,p)]=c
print(f"{'endpoint':46} " + " ".join(f"{r[:6]:>6}" for r in roles))
for m,p in EPS:
    print(f"{m+' '+p[:42]:46} " + " ".join(f"{res.get((r,p),'-'):>6}" for r in roles))
