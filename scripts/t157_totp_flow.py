import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
ME="golden-snow-4771@bugcrowdninja.com"
def req(path,body):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H',BB,'-H','Content-Type: application/json','-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== 1. set my mfa_preference to totp (needed before create-totp-factor) ===")
c,b=req('/api/v1/users/mfa-preference',{"credentials":{"email":ME,"password":"Tester","mfa_type":"totp"}})
print(f"  {c} {b[:300].replace(chr(10),' ')}")
print("\n=== 2. create-totp-factor for MY account ===")
c,b=req('/api/v1/users/create-totp-factor',{"credentials":{"email":ME,"password":"Tester"}})
print(f"  {c}")
print(f"  {b[:600].replace(chr(10),' ')}")
if c=='200':
    try:
        d=json.loads(b)
        print("\n  KEYS:",list(d.keys()))
        print("  data:",json.dumps(d.get('data'))[:300])
        print("  userSid:",d.get('userSid'))
        open('/tmp/totp.json','w').write(json.dumps(d))
    except Exception as e: print("  parse",e)
