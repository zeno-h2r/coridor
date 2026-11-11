import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
def get(p,tok):
    cmd=['curl','-s','-m','25','-o','/tmp/b','-w','%{http_code}',H+p,'-H','token: '+tok,'-H',BB]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
TT=open('/tmp/bac_TESTER').read().strip()
print("=== control: can Tester read user 1's OTHER resources? ===")
for p in ['/api/v1/users/1','/api/v1/issues/121','/api/v1/controls/1','/api/v1/risks/1']:
    c,b=get(p,TT)
    print(f"  {c} {p}")
print()
print("=== but timesheet entries for user 1: ===")
c,b=get('/api/v1/timesheet_entries/43',TT)
print(f"  {c} /api/v1/timesheet_entries/43 (user 1's entry)")
try:
    o=json.loads(b)['timesheet_entries'][0]
    print(f"    user_id={o.get('user_id')} date={o.get('date')} hours={o.get('hours')}")
    print(f"    timesheetable_meta={json.dumps(o.get('timesheetable_meta'))[:200]}")
except: pass
print()
print("=== full field dump of one foreign entry ===")
c,b=get('/api/v1/timesheet_entries/43',TT)
o=json.loads(b)['timesheet_entries'][0]
for k,v in o.items():
    if isinstance(v,(str,int,float,bool,type(None))) and v not in ('',None):
        print(f"  {k:24} = {str(v)[:80]!r}")
