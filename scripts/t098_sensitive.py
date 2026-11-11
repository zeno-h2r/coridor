import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def post(path,body):
    cmd=['curl','-s','-m','90','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-AuditBoard-Source: SchemaTable Rows','-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
for ent in ['user','document_version','issue']:
    c,txt=post(f'/api/v1/table/query?entities={ent}',
        {"ab:query":{"entities":[ent],"filter":{},"include":[ent],"page":{"size":1}}})
    print(f"===== {ent}: {c} len={len(txt)}")
    try:
        d=json.loads(txt); inc=d.get('included') or []
        if inc:
            a=inc[0].get('attributes') or {}
            print("  attr keys:",sorted(a.keys())[:40])
            for k in ['email','name','title','description','body','content','text','fullName','username','key','url']:
                if k in a: print(f"   {k} = {str(a[k])[:150]}")
    except Exception as e: print("  err",e,txt[:200])
    print()
