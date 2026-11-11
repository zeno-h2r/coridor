import json,subprocess,os
from collections import Counter
H=os.environ['H']; BB=os.environ['BB']
tok=open('/tmp/bac_TESTER').read().strip()
cmd=['curl','-s','-m','30',H+'/api/v1/timesheet_entries','-H','token: '+tok,'-H',BB]
d=json.loads(subprocess.run(cmd,capture_output=True,text=True).stdout)
ts=d['timesheet_entries']
print(f"Tester sees {len(ts)} timesheet entries")
print("keys:",sorted(ts[0].keys()))
print()
# whose are they?
for k in ['user_id','user','timesheetable_id','timesheetable_type','project_id','task_id']:
    vals=Counter(str(t.get(k)) for t in ts)
    if len(vals)>1 or (list(vals)[0]!='None'):
        print(f"  {k}: {dict(list(vals.most_common(8)))}")
print()
print("sample rows:")
for t in ts[:3]:
    print("  ",json.dumps({k:t.get(k) for k in ['id','user_id','date','hours','comment','timesheetable_type','timesheetable_id']})[:200])
