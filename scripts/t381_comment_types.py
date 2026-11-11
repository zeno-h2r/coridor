import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
def get(p):
    cmd=['curl','-s','-m','25','-o','/tmp/b','-w','%{http_code}',H+p,'-H','token: '+TOK,'-H',BB]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
c,b=get('/api/v1/comments')
d=json.loads(b)
cs=d['comments']
from collections import Counter
print(f"total comments: {len(cs)}")
print("by commentable_type:",dict(Counter(x.get('commentable_type') for x in cs)))
print()
print("=== all commentable types seen, with sample raw/html ===")
seen=set()
for x in cs:
    t=x.get('commentable_type')
    if t in seen: continue
    seen.add(t)
    print(f"  {t} (id {x.get('commentable_id')}):")
    print(f"     html={x.get('message_html')!r}")
    print(f"     raw ={x.get('message_raw')!r}")
