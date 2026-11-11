import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def post(path,body):
    cmd=['curl','-s','-m','90','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-AuditBoard-Source: SchemaTable Rows','-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
for ent in ['narrative','issue']:
    c,b=post(f'/api/v1/table/query?entities={ent}',{"ab:query":{"entities":[ent],"filter":{},"include":[ent]}})
    try:
        d=json.loads(b); inc=d.get('included') or []
        print(f"{ent}: {c} count={len(inc)} ids={[i['id'] for i in inc][:10]}")
    except Exception as e: print(f"{ent}: {c} {b[:150]}")
