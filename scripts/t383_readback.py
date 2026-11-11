import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
cmd=['curl','-s','-m','25',H+'/api/v1/comments','-H','token: '+TOK,'-H',BB]
d=json.loads(subprocess.run(cmd,capture_output=True,text=True).stdout)
cs=d['comments']
print(f"total: {len(cs)}")
print("\n=== newest 12 comments: html vs raw ===")
for c in sorted(cs,key=lambda x:int(x['id']),reverse=True)[:12]:
    print(f"  id={c['id']:<4} type={str(c.get('commentable_type'))[:18]:20}")
    print(f"        html={str(c.get('message_html'))[:70]!r}")
    print(f"        raw ={str(c.get('message_raw'))[:70]!r}")
