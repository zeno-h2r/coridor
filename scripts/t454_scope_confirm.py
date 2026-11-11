import json,subprocess,os
from collections import Counter
H=os.environ['H']; BB=os.environ['BB']
def get(p,tok):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}',H+p,'-H','token: '+tok,'-H',BB]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== who can read ALL timesheet entries? ===")
for r in ['OWNER','SYSADMIN','TESTER']:
    tok=open(f'/tmp/bac_{r}').read().strip()
    c,b=get('/api/v1/timesheet_entries',tok)
    n=0; users=set()
    try:
        ts=json.loads(b)['timesheet_entries']; n=len(ts)
        users={t.get('user_id') for t in ts}
    except: pass
    print(f"  {r:9} {c}  entries={n:<5} distinct_users={len(users)}  users={sorted(users)[:10]}")
print()
print("=== is there a filter that scopes to self? (control) ===")
tok=open('/tmp/bac_TESTER').read().strip()
for q in ['?filter[user_id][eq]=170','?user_id=170','?filter[user_id][eq]=1']:
    c,b=get('/api/v1/timesheet_entries'+q,tok)
    n=0; users=set()
    try:
        ts=json.loads(b)['timesheet_entries']; n=len(ts); users={t.get('user_id') for t in ts}
    except: pass
    print(f"  TESTER {q:32} -> {c} entries={n} users={sorted(users)[:5]}")
print()
print("=== what's in the comment field (free text)? ===")
c,b=get('/api/v1/timesheet_entries',tok)
ts=json.loads(b)['timesheet_entries']
withc=[t for t in ts if t.get('comment')]
print(f"  entries with comments: {len(withc)}")
for t in withc[:5]:
    print(f"    user={t.get('user_id')} date={t.get('date')} comment={str(t.get('comment'))[:80]!r}")
