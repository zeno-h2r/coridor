import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
cmd=['curl','-s','-m','25',H+'/api/v1/comments','-H','token: '+TOK,'-H',BB]
d=json.loads(subprocess.run(cmd,capture_output=True,text=True).stdout)
for c in d['comments']:
    if c.get('id')=='903':
        print("=== comment 903 (our injected one) ===")
        print(f"  message_html : {c.get('message_html')!r}")
        print(f"  message_raw  : {c.get('message_raw')!r}")
        print(f"  commentable  : {c.get('commentable_type')} #{c.get('commentable_id')}")
        print(f"  owner_user_id: {c.get('owner_user_id')}")
        print()
        print("  -> server-side sanitizer produced message_html = '<img />' (tag stripped, handler gone)")
        print("  -> but message_raw retains the entity-encoded original")
        print("  -> client renders message_raw -> browser decodes &lt; -> live <img onerror>")
        break
print()
print("=== compare with a benign comment ===")
for c in d['comments']:
    if c.get('id')!='903' and c.get('message_raw'):
        print(f"  id={c['id']} html={c.get('message_html')!r} raw={c.get('message_raw')!r}")
        break
