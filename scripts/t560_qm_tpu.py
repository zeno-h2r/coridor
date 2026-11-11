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
print("=== TPU across suggestable ids (does any return data?) ===")
for sid in [38,39,40,47,31,1,2]:
    body={"suggestable_type":"Narrative","suggestable_id":sid,"suggested_type":"ControlsDatum"}
    c,b=req(body,TOK['TPU'])
    n=0; tot=0
    try:
        d=json.loads(b); n=len(d.get('data') or []); tot=(d.get('meta') or {}).get('total',0)
    except: pass
    print(f"  TPU narrative {sid:3} -> {c} rows={n} total={tot}")
print()
print("=== and TESTER for the same ids (control) ===")
for sid in [38,39,40,47,31]:
    body={"suggestable_type":"Narrative","suggestable_id":sid,"suggested_type":"ControlsDatum"}
    c,b=req(body,TOK['TESTER'])
    n=0
    try: n=len(json.loads(b).get('data') or [])
    except: pass
    print(f"  TESTER narrative {sid:3} -> {c} rows={n}")
print()
print("=== what does the 24-row payload contain? (Tester) ===")
body={"suggestable_type":"Narrative","suggestable_id":38,"suggested_type":"ControlsDatum"}
c,b=req(body,TOK['TESTER'])
d=json.loads(b)
rows=d.get('data') or []
print(f"  rows={len(rows)}")
if rows:
    a=rows[0].get('attributes') or {}
    print(f"  keys={sorted(a.keys())[:18]}")
    for k in ['name','idCode','description','controlObjective']:
        if k in a: print(f"    {k}={str(a[k])[:90]!r}")
