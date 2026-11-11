import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
cmd=['curl','-s','-m','25',H+'/api/v1/comments','-H','token: '+TOK,'-H',BB]
d=json.loads(subprocess.run(cmd,capture_output=True,text=True).stdout)
for c in d['comments']:
    if str(c['id'])=='914':
        print("=== comment 914 ===")
        print(f"  message_html = {c.get('message_html')!r}")
        print(f"  message_raw  = {c.get('message_raw')!r}")
        print(f"  commentable  = {c.get('commentable_type')} {c.get('commentable_id')}")
        break
