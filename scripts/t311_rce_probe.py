import json,subprocess,os
from concurrent.futures import ThreadPoolExecutor
H=os.environ['H']; BB=os.environ['BB']
TOK={r:open(f'/tmp/bac_{r}').read().strip() for r in ['OWNER','SYSADMIN','TESTER','TPU']}
def req(args):
    r,m,p,body=args
    cmd=['curl','-s','-m','20','-o','/tmp/b_%s'%r,'-w','%{http_code}','-X',m,H+p,
         '-H','token: '+TOK[r],'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    try: t=open('/tmp/b_%s'%r,encoding='utf-8',errors='replace').read()
    except: t=''
    return r,m,p,c,t[:150]
EPS=[
 ('POST','/api/v1/assessments/1/run_scoring_agent',{}),
 ('POST','/api/v1/entities/1/migrate/run',{}),
 ('POST','/api/v1/score_types/migrate/run',{}),
 ('POST','/api/v1/frameworks/migrate-ucf-frameworks',{}),
 ('POST','/api/v1/role_permissions/queue_permissions_syncer',{}),
 ('POST','/api/v1/controls_data/implement/async',{}),
 ('POST','/api/v1/generative/create_entity',{}),
 ('POST','/api/v1/generative/dynamic-schema',{}),
 ('POST','/api/v1/generative/batch-summaries',{}),
 ('POST','/api/v1/generative/scoping-memo',{}),
 ('POST','/api/v1/generative/stream',{}),
 ('POST','/api/v1/regulations/validate_custom_entity',{}),
 ('POST','/api/v1/field_mappings/validate',{}),
 ('POST','/api/v1/import_tools/validate',{}),
 ('POST','/api/v1/vendor_summary_reports/generate',{}),
 ('POST','/api/v1/markup_samples/export/excel',{}),
 ('POST','/api/v1/policies/1/ssp_generation',{}),
 ('POST','/api/v1/tests/1/midship_launch',{}),
]
jobs=[(r,m,p,b) for m,p,b in EPS for r in TOK]
print(f"{'endpoint':52} " + " ".join(f"{r[:7]:>7}" for r in TOK))
res={}
with ThreadPoolExecutor(max_workers=10) as ex:
    for r,m,p,c,t in ex.map(req,jobs): res[(r,p)]=(c,t)
for m,p,b in EPS:
    print(f"{m+' '+p[:46]:52} " + " ".join(f"{res[(r,p)][0]:>7}" for r in TOK))
print("\n--- notable response bodies ---")
seen=set()
for m,p,b in EPS:
    for r in TOK:
        c,t=res[(r,p)]
        if c in ('200','201','202') and (p,c) not in seen:
            seen.add((p,c)); print(f"  [{r}] {c} {p}\n      {t[:140]}")
