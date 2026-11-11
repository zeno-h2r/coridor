import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== passwordless_invitations/redeem (hidden endpoint) ===")
for body in [{}, {"token":"x"}, {"token":"1"}, {"token":"00000000-0000-0000-0000-000000000000"}]:
    c,b=req('POST','/api/v1/passwordless_invitations/redeem',body)
    print(f"  {json.dumps(body)[:50]:52} -> {c} {b[:220].replace(chr(10),' ')}")
print("\n=== passwordless_invitations/request_new ===")
for body in [{}, {"email":"golden-leaf-3068@bugcrowdninja.com"}]:
    c,b=req('POST','/api/v1/passwordless_invitations/request_new',body)
    print(f"  {json.dumps(body)[:50]:52} -> {c} {b[:220].replace(chr(10),' ')}")
