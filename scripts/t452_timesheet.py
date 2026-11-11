import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
def get(p,tok):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}',H+p,'-H','token: '+tok,'-H',BB]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== timesheet_entries: what does it actually return? ===")
for r in ['OWNER','SYSADMIN','TESTER']:
    tok=open(f'/tmp/bac_{r}').read().strip()
    c,b=get('/api/v1/timesheet_entries',tok)
    print(f"\n  {r:9} {c} len={len(b)}")
    try:
        d=json.loads(b)
        for k in d:
            if isinstance(d[k],list):
                print(f"    key={k} n={len(d[k])}")
                if d[k]: print(f"      sample={json.dumps(d[k][0])[:220]}")
    except Exception as e: print("   ",b[:150])
