import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TOK={r:open(f'/tmp/bac_{r}').read().strip() for r in ['OWNER','SYSADMIN','TESTER','TPU']}
def req(body,tok):
    cmd=['curl','-s','-m','120','-o','/tmp/b','-w','%{http_code}','-X','POST',
         H+'/api/v1/suggestions/query-matches',
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== is Owner's 0 a permission thing or a data thing? ===")
body={"suggestable_type":"Narrative","suggestable_id":38,"suggested_type":"ControlsDatum"}
for r in ['OWNER','SYSADMIN','TESTER','TPU']:
    c,b=req(body,TOK[r])
    d=json.loads(b) if c=='200' else {}
    meta=d.get('meta') or {}
    print(f"  {r:9} -> {c} data={len(d.get('data') or [])} meta.total={meta.get('total')} statuses={meta.get('statuses')}")
print()
print("=== does Owner see the suggestions themselves? ===")
for r in ['OWNER','TESTER']:
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}',H+'/api/v1/suggestions','-H','token: '+TOK[r],'-H',BB]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    b=open('/tmp/b',encoding='utf-8',errors='replace').read()
    n=0
    try: n=len(json.loads(b).get('suggestions') or [])
    except: pass
    print(f"  {r:9} GET /suggestions -> {c} rows={n}")
print()
print("=== Owner RBAC for suggestion / controlsDatum ===")
cmd=['curl','-s','-m','30',H+'/api/v1/role_permissions?role_id=5','-H','token: '+TOK['OWNER'],'-H',BB]
rp=json.loads(subprocess.run(cmd,capture_output=True,text=True).stdout)['role_permissions']
for key in ['suggestion','controlsDatum','control']:
    hits=[x for x in rp if key.lower() in str(x.get('key','')).lower()][:4]
    print(f"  role5 '{key}': {[(h.get('key'),h.get('value')) for h in hits]}")
