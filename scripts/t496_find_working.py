import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
TO=open('/tmp/bac_OWNER').read().strip()
print("=== list suggestions with their suggestable_type (which process cleanly?) ===")
c,b=req('GET','/api/v1/suggestions',tok=TO)
d=json.loads(b)
sug=d.get('suggestions') or []
from collections import Counter
print(f"  total: {len(sug)}")
print("  by suggestable_type:",dict(Counter(s.get('suggestable_type') for s in sug)))
print("  by status:",dict(Counter(s.get('status') for s in sug)))
print()
print("  sample rows:")
for s in sug[:8]:
    print(f"    id={s['id']:<4} type={str(s.get('suggestable_type')):14} sid={s.get('suggestable_id'):<5} status={s.get('status')} suggested={s.get('suggested_type')}#{s.get('suggested_id')}")
