import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H',BB,'-H','Content-Type: application/json']
    if tok: cmd+=['-H','token: '+tok]
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== reset-token-info (UNAUTH, reset_token param) ===")
for rt in ['abc','1','0','0000000000000000000000000000000000000000','aaaa-bbbb']:
    c,t=req('GET',f'/api/v1/users/reset-token-info?reset_token={rt}')
    print(f"  reset_token={rt[:24]:26} -> {c}  {t[:200].replace(chr(10),' ')}")
print("\n=== with auth token ===")
c,t=req('GET','/api/v1/users/reset-token-info?reset_token=abc',tok=T)
print(f"  -> {c} {t[:250].replace(chr(10),' ')}")
