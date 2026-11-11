import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
def get(p,tok):
    cmd=['curl','-s','-m','25','-o','/tmp/b','-w','%{http_code}',H+p,'-H','token: '+tok,'-H',BB]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== can OWNER read plans 154/155 directly by id? ===")
for r in ['OWNER','TESTER','TPU']:
    tok=open(f'/tmp/bac_{r}').read().strip()
    for pid in [154,155,156]:
        c,b=get(f'/api/v1/project_plans/{pid}',tok)
        nm=''
        try: nm=str(json.loads(b)['project_plans'][0].get('name'))[:30]
        except: pass
        print(f"  {r:9} /project_plans/{pid} -> {c} {nm}")
    print()
print("=== full record of 154 as Tester ===")
tok=open('/tmp/bac_TESTER').read().strip()
c,b=get('/api/v1/project_plans/154',tok)
try:
    o=json.loads(b)['project_plans'][0]
    for k,v in o.items():
        if isinstance(v,(str,int,float,bool,type(None))) and v not in ('',None):
            print(f"  {k:26} = {str(v)[:70]!r}")
except Exception as e: print("  ",c,b[:200])
