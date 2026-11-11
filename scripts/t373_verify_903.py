import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
cmd=['curl','-s','-m','25',H+'/api/v1/comments','-H','token: '+TOK,'-H',BB]
d=json.loads(subprocess.run(cmd,capture_output=True,text=True).stdout)
cs=d['comments']
print(f"comments returned: {len(cs)}  ids: {[c.get('id') for c in cs]}")
for c in cs:
    if c.get('id')=='903':
        print("\n=== comment 903 ===")
        for k in ['id','message_html','message_raw','commentable_type','commentable_id','owner_user_id','type','created_at']:
            print(f"  {k:18} = {c.get(k)!r}")
