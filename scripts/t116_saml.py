import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None,follow=False):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}|%{redirect_url}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if follow: cmd.insert(1,'-L')
    if body is not None: cmd+=['-d',json.dumps(body)]
    out=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return out, open('/tmp/b',encoding='utf-8',errors='replace').read()
for p in ['/api/v1/sso/saml/login','/api/v1/sso/saml/login?redirect=/sh/admin/settings',
          '/api/v1/sso/saml/idps','/api/v1/sso/saml']:
    c,b=req('GET',p)
    print(f"{c}  GET {p}")
    print("   ",b[:250].replace(chr(10),' '))
print()
# open-redirect probe on the redirect param
for r in ['https://evil.example.com','//evil.example.com','/\\evil.example.com','https://webhook.site/d5ca52ae-fe37-478e-9d77-7501ac90b9b2/saml']:
    c,b=req('GET','/api/v1/sso/saml/login?redirect='+r)
    print(f"redirect={r[:45]:47} -> {c}")
