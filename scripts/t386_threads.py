import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
cmd=['curl','-s','-m','25',H+'/api/v1/comments','-H','token: '+TOK,'-H',BB]
d=json.loads(subprocess.run(cmd,capture_output=True,text=True).stdout)
cs=d['comments']
print("=== comments with payloads: which thread? ===")
for c in cs:
    raw=str(c.get('message_raw') or '')
    if 'ZXJ' in raw or 'ZXS' in raw or 'javascript' in raw or 'onerror' in raw:
        print(f"  id={c['id']:<4} parent={c.get('parent_comment_id')} type={c.get('commentable_type')} cid={c.get('commentable_id')} status={c.get('status')!r}")
        print(f"        html={c.get('message_html')!r}")
        print(f"        raw ={raw[:80]!r}")
