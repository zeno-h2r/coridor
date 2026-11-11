import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
V="golden-leaf-3068@bugcrowdninja.com"
print("=== reset-token-info variants ===")
for m,p,b in [
 ('GET',f'/api/v1/users/reset-token-info?token=abc',None),
 ('GET',f'/api/v1/users/reset-token-info?token=1',None),
 ('POST','/api/v1/users/reset-token-info',{"reset_token":"abc"}),
 ('POST','/api/v1/users/reset-token-info',{"token":"abc","email":V}),
 ('GET',f'/api/v1/users/reset-token-info/1',None),
]:
    c,t=req(m,p,b)
    print(f"  {c} {m:5} {p}  {t[:180].replace(chr(10),' ')}")
print("\n=== password-reset-email response (does it leak token?) ===")
c,t=req('POST','/api/v1/users/password-reset-email',{"email":V})
print(f"  {c} {t[:400]}")
print("\n=== verify-totp-registration / mfa-preference shapes ===")
for m,p,b in [
 ('POST','/api/v1/users/verify-totp-registration',{}),
 ('POST','/api/v1/users/verify-totp-registration',{"credentials":{"email":V},"code":"123456"}),
 ('POST','/api/v1/users/mfa-preference',{"credentials":{"email":V,"password":"Tester"},"mfa_type":"totp"}),
]:
    c,t=req(m,p,b)
    print(f"  {c} {m:5} {p}")
    print(f"      {t[:260].replace(chr(10),' ')}")
