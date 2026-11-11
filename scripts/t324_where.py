import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
T=open('/tmp/bac_OWNER').read().strip()
def get(p):
    cmd=['curl','-s','-m','30',H+p,'-H','token: '+T,'-H',BB]
    return subprocess.run(cmd,capture_output=True,text=True).stdout
c=get('/api/v1/controls/1')
try:
    o=json.loads(c)['controls'][0]
    print("control 1 keys:",sorted(o.keys())[:30])
    for k in ['id','name','description','workspace_id','company_id','process_id','auditable_entity_id','controls_datum_id','cycle_id','scope']:
        if k in o: print(f"  {k} = {str(o[k])[:120]}")
except Exception as e: print("err",e,c[:300])
