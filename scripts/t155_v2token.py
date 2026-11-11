import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None,hdr=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H',BB,'-H','Content-Type: application/json','-H','Accept: application/vnd.api+json']
    if hdr:
        for k,v in hdr.items(): cmd+=['-H',f'{k}: {v}']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== /api/v2/auth with TOKEN header ===")
for label,h in [("v1 token",{'TOKEN':T}),("garbage",{'TOKEN':'x'}),("empty",{'TOKEN':''})]:
    c,t=req('GET','/api/v2/auth',hdr=h)
    print(f"  {label:10} -> {c}  {t[:250].replace(chr(10),' ')}")
print("\n=== POST /api/v2/auth with TOKEN (mintedSession adoption) ===")
for label,h,b in [("self token",{'TOKEN':T},{"mintedSession":{"token":T}}),
                  ("self token2",{'TOKEN':T},{"credentials":{"email":"golden-snow-4771@bugcrowdninja.com","password":"Tester"}})]:
    c,t=req('POST','/api/v2/auth',b,hdr=h)
    print(f"  {label:12} -> {c}  {t[:300].replace(chr(10),' ')}")
