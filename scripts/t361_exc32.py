import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_OWNER').read().strip()
def get(p):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}',H+p,'-H','token: '+TOK,'-H',BB]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== exception 32 via several route shapes ===")
for p in ['/api/v1/exception_requests/32','/api/v1/exceptions/32',
          '/api/v1/exception_requests?filter[id][eq]=32']:
    c,b=get(p)
    print(f"\n  {c} {p}  len={len(b)}")
    if c=='200':
        try:
            d=json.loads(b)
            arr=d.get('exception_requests') or d.get('exceptions') or []
            if arr:
                o=arr[0]
                print(f"    keys: {sorted(o.keys())[:40]}")
                for k in ['id','name','title','description','reason','status','justification','notes','risk_rating','impact']:
                    if k in o: print(f"    {k} = {str(o[k])[:120]!r}")
                open('/tmp/exc32.json','w').write(json.dumps(o))
        except Exception as e: print("    parse",e,b[:200])
