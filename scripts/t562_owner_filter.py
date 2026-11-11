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
print("=== repeat 3x: Owner total=24 data=0 vs Tester data=24 ===")
for i in range(3):
    body={"suggestable_type":"Narrative","suggestable_id":38,"suggested_type":"ControlsDatum"}
    c1,b1=req(body,TOK['OWNER']); d1=json.loads(b1)
    c2,b2=req(body,TOK['TESTER']); d2=json.loads(b2)
    print(f"  run{i+1}: OWNER {c1} data={len(d1.get('data') or [])} total={(d1.get('meta') or {}).get('total')}"
          f"  |  TESTER {c2} data={len(d2.get('data') or [])} total={(d2.get('meta') or {}).get('total')}")
print()
print("=== across narratives: is Owner always 0 while total>0? ===")
for sid in [38,39,40,47,31]:
    body={"suggestable_type":"Narrative","suggestable_id":sid,"suggested_type":"ControlsDatum"}
    c1,b1=req(body,TOK['OWNER']); d1=json.loads(b1)
    c2,b2=req(body,TOK['TESTER']); d2=json.loads(b2)
    print(f"  narrative {sid:3}: OWNER data={len(d1.get('data') or []):<3} total={(d1.get('meta') or {}).get('total'):<3}"
          f" | TESTER data={len(d2.get('data') or []):<3} total={(d2.get('meta') or {}).get('total')}")
