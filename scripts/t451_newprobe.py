import json,subprocess,os
from concurrent.futures import ThreadPoolExecutor
H=os.environ['H']; BB=os.environ['BB']
T=open('/tmp/bac_OWNER').read().strip()
def one(args):
    m,p=args
    cmd=['curl','-s','-m','15','-o','/tmp/nb','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if m=='POST': cmd+=['-d','{}']
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    try: t=open('/tmp/nb',encoding='utf-8',errors='replace').read()[:90]
    except: t=''
    return m,p,c,t
EPS=[
 ('POST','/graphql'),('POST','/api/graphql'),('GET','/graphql'),('POST','/api/v2/graphql'),
 ('GET','/api/v2/auditable-entity'),('GET','/api/v2/auditable-entity/coverage-roll-up'),
 ('GET','/api/v2/user/231/avatar'),('GET','/api/v2/ml-trace/1'),
 ('GET','/api/v1/search'),('GET','/api/v1/search?q=admin'),
 ('POST','/api/v1/table/export'),('POST','/api/v1/table/_op/async_export'),
 ('GET','/api/v1/webhook_urls'),('GET','/api/v1/webhook_urls/1'),
 ('GET','/api/v1/integrations'),('GET','/api/v1/integrations/available-services'),
 ('GET','/api/v1/timesheet_entries'),('GET','/api/v1/timesheets'),
 ('GET','/api/v1/work-tasks'),('GET','/api/v1/we_tasks'),
 ('GET','/api/v1/notifications'),('GET','/api/v1/inbox'),
 ('GET','/api/v1/saved_prompts'),('GET','/api/v1/assistant/saved-prompts'),
 ('GET','/api/v1/sigma_reports'),('GET','/api/v1/sigma_workbooks'),
 ('GET','/api/v1/markup_test_sheets'),('GET','/api/v1/markup_samples'),
 ('GET','/api/v1/project_plans'),('GET','/api/v1/project_plan_containers'),
 ('GET','/api/v1/rcw_requests'),('GET','/api/v1/rcw_library_requests'),
 ('GET','/api/v1/financial_accounts'),('GET','/api/v1/financial_applications'),
 ('GET','/api/v1/bookings'),('GET','/api/v1/user_skills'),('GET','/api/v1/skills'),
 ('GET','/api/v1/import_records'),('GET','/api/v1/guided_summary_reports'),
 ('GET','/api/v1/cross_audit_summaries'),('GET','/api/v1/audit_surveys'),
]
print(f"{'endpoint':56} {'code':>5}  body")
with ThreadPoolExecutor(max_workers=10) as ex:
    for m,p,c,t in ex.map(one,EPS):
        mark='  <<<' if c in ('200','201','202') else ''
        print(f"{m+' '+p[:50]:56} {c:>5}  {t[:70]}{mark}")
