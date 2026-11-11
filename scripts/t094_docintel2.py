import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','90','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
# find a Policy / ProjectPlanContainer id I can use
for ent in ['policy','project_plan_container']:
    c,b=req('POST',f'/api/v1/table/query?entities={ent}',{"ab:query":{"entities":[ent],"filter":{}}})
    try:
        d=json.loads(b); ids=[r['id'] for r in d['data']][:5]
        print(f"{ent}: {c} ids={ids}")
    except: print(f"{ent}: {c} {b[:200]}")
