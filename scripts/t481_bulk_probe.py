import json,subprocess,os
from concurrent.futures import ThreadPoolExecutor
H=os.environ['H']; BB=os.environ['BB']
TOK={r:open(f'/tmp/bac_{r}').read().strip() for r in ['OWNER','SYSADMIN','TESTER','TPU']}
def one(a):
    r,m,p,b=a
    cmd=['curl','-s','-m','20','-o','/tmp/bb_%s'%r,'-w','%{http_code}','-X',m,H+p,
         '-H','token: '+TOK[r],'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if b is not None: cmd+=['-d',json.dumps(b)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    try: t=open('/tmp/bb_%s'%r,encoding='utf-8',errors='replace').read()[:100]
    except: t=''
    return r,p,c,t
EPS=[
 ('POST','/api/v1/suggestions/bulk-accept',{"suggestion_ids":[1]}),
 ('POST','/api/v1/suggestions/bulk-reject',{"suggestion_ids":[1]}),
 ('POST','/api/v1/esg_metric_values/bulk-delete',{"ids":[1]}),
 ('POST','/api/v1/controls_datum_framework_items/bulk_set_disabled',{"ids":[1],"disabled":True}),
 ('POST','/api/v1/policy_controls_datum_mappings/bulk_accept',{"ids":[1]}),
 ('POST','/api/v1/policy_framework_item_mappings/bulk_accept',{"ids":[1]}),
 ('POST','/api/v1/program_regulation_items/bulk_update',{"ids":[1]}),
 ('POST','/api/v1/key_risk_indicator_request_updates/bulk_upsert',{"updates":[]}),
 ('POST','/api/v1/key_performance_indicator_request_updates/bulk_upsert',{"updates":[]}),
 ('POST','/api/v1/auditable_entities/bulk_add_recurring_questionnaire',{"ids":[1]}),
 ('POST','/api/v1/framework_items/bulk-complete-version-mapping',{"ids":[1]}),
 ('POST','/api/v1/ticketing/tickets/bulk',{"create_ticket_payloads":[]}),
 ('POST','/api/v1/risks/bulk_update',{"ids":[1],"updates":{}}),
 ('POST','/api/v1/controls/bulk_update',{"ids":[1],"updates":{}}),
 ('POST','/api/v1/issues/bulk_update',{"ids":[1],"updates":{}}),
]
jobs=[(r,m,p,b) for m,p,b in EPS for r in TOK]
res={}
with ThreadPoolExecutor(max_workers=10) as ex:
    for r,p,c,t in ex.map(one,jobs): res[(r,p)]=(c,t)
print(f"{'endpoint':56} " + " ".join(f"{r[:7]:>7}" for r in TOK))
for m,p,b in EPS:
    line=f"{m+' '+p[:50]:56} " + " ".join(f"{res[(r,p)][0]:>7}" for r in TOK)
    if any(res[(r,p)][0] in ('200','201','202') for r in TOK): line+="  <<<"
    print(line)
print()
print("=== bodies for any 2xx ===")
for m,p,b in EPS:
    for r in TOK:
        c,t=res[(r,p)]
        if c in ('200','201','202'):
            print(f"  [{r}] {c} {p}\n      {t[:130]}")
