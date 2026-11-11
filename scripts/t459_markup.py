import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
def get(p,tok):
    cmd=['curl','-s','-m','25','-o','/tmp/b','-w','%{http_code}',H+p,'-H','token: '+tok,'-H',BB]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== markup_test_sheets / markup_samples: what's in them? ===")
for r in ['OWNER','TESTER','TPU']:
    tok=open(f'/tmp/bac_{r}').read().strip()
    for p in ['/api/v1/markup_test_sheets','/api/v1/markup_samples']:
        c,b=get(p,tok)
        n=0; sample=''
        try:
            d=json.loads(b)
            for k in d:
                if isinstance(d[k],list):
                    n=len(d[k])
                    if d[k]: sample=json.dumps(d[k][0])[:180]
        except: pass
        print(f"  {r:9} {c} {p:32} n={n}")
        if sample: print(f"      {sample}")
