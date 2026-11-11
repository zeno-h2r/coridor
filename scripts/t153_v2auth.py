import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H',BB,'-H','Content-Type: application/json','-H','Accept: application/vnd.api+json']
    if tok: cmd+=['-H','token: '+tok]
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
E="golden-snow-4771@bugcrowdninja.com"
print("=== /api/v2/auth plane ===")
for m,p,b in [
 ('GET','/api/v2/auth',None),
 ('POST','/api/v2/auth',{}),
 ('POST','/api/v2/auth',{"credentials":{"email":E,"password":"Tester"}}),
 ('POST','/api/v2/auth/login',{"credentials":{"email":E,"password":"Tester"}}),
 ('DELETE','/api/v2/auth/logout',{}),
]:
    c,t=req(m,p,b)
    print(f"  {c} {m:6} {p}")
    print(f"      {t[:300].replace(chr(10),' ')}")
print("\n=== mintedSession shape (from bundle authenticate) ===")
for b in [{"mintedSession":{"token":"x"}},{"mintedSession":{"user_id":"231","token":"231:abc"}},
          {"credentials":{"mintedSession":{"token":"x"}}}]:
    c,t=req('POST','/api/v2/auth',b)
    print(f"  {json.dumps(b)[:70]:72} -> {c} {t[:180].replace(chr(10),' ')}")
