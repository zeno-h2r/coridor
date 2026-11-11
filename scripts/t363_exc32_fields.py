import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
def get(p):
    cmd=['curl','-s','-m','25','-H','token: '+TOK,'-H',BB,H+p]
    return json.loads(subprocess.run(cmd,capture_output=True,text=True).stdout)
d=get('/api/v1/exception_requests/32')
o=d['exception_requests'][0]
print("=== exception 32 ===")
print("keys:",sorted(o.keys()))
print()
for k in sorted(o.keys()):
    v=o[k]
    if isinstance(v,(str,int,float,bool,type(None))) and v not in ('',None,0,False):
        print(f"  {k:34} = {str(v)[:110]!r}")
print()
print("permissions:",json.dumps(o.get('_permissions')))
open('/tmp/exc32.json','w').write(json.dumps(o))
