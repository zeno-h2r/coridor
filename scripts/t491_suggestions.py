import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-AuditBoard-Source: SchemaTable Rows']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== suggestions plane by role ===")
for r in ['OWNER','SYSADMIN','TESTER','TPU']:
    tok=open(f'/tmp/bac_{r}').read().strip()
    for p in ['/api/v1/suggestions','/api/v1/suggestions/query-matches']:
        c,b=req('GET',p,tok=tok)
        n=0; sample=''
        try:
            d=json.loads(b)
            for k in d:
                if isinstance(d[k],list):
                    n=len(d[k])
                    if d[k]: sample=json.dumps(d[k][0])[:160]
        except: pass
        print(f"  {r:9} {c} {p:32} n={n}")
        if sample: print(f"      {sample}")
