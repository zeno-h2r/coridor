import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
def get(p):
    cmd=['curl','-s','-m','25','-o','/tmp/b','-w','%{http_code}',H+p,'-H','token: '+TOK,'-H',BB]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== find the comment record on exception 32 ===")
for p in ['/api/v1/exception_requests/32/comments','/api/v1/comments?filter[commentable_id][eq]=32',
          '/api/v1/comments','/api/v1/exception_requests/32?include=comments']:
    c,b=get(p)
    print(f"\n  {c} {p}  len={len(b)}")
    if c=='200' and len(b)<4000: print(f"    {b[:500]}")
    elif c=='200':
        try:
            d=json.loads(b)
            for k in d:
                if isinstance(d[k],list) and d[k]:
                    print(f"    key={k} n={len(d[k])} sample={json.dumps(d[k][0])[:300]}")
        except: pass
