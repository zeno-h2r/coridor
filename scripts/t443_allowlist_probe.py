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
tag='ZXA'+uuid.uuid4().hex[:5]
print("=== what tags survive the server sanitizer in message_html? ===")
# WAF blocks img/svg/script/onerror. Test img WITHOUT onerror to map the allowlist.
probes=[
 ('img-plain',   f'<img src=x>{tag}'),
 ('img-slash',   f'<img/src=x>{tag}'),
 ('b',           f'<b>{tag}</b>'),
 ('i',           f'<i>{tag}</i>'),
 ('u',           f'<u>{tag}</u>'),
 ('strong',      f'<strong>{tag}</strong>'),
 ('em',          f'<em>{tag}</em>'),
 ('span',        f'<span>{tag}</span>'),
 ('div',         f'<div>{tag}</div>'),
 ('p',           f'<p>{tag}</p>'),
 ('br',          f'<br>{tag}'),
 ('a-http',      f'<a href="https://x.com">{tag}</a>'),
 ('table',       f'<table><tr><td>{tag}</td></tr></table>'),
 ('ul',          f'<ul><li>{tag}</li></ul>'),
 ('h1',          f'<h1>{tag}</h1>'),
 ('code',        f'<code>{tag}</code>'),
 ('pre',         f'<pre>{tag}</pre>'),
 ('blockquote',  f'<blockquote>{tag}</blockquote>'),
]
for label,h in probes:
    c,b=post(h)
    st=''
    if c in ('200','201'):
        try: st=repr(json.loads(b)['comments'][0].get('message_html'))[:70]
        except: pass
    print(f"  {label:12} {c:>4}  {st}")
