import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
for p in ['/api/v1/asset_match_mappings/auditboard_fields','/api/v1/field_mappings/configuration']:
    c,b=req('GET',p)
    print(f"=== {c} GET {p}")
    print("   ",b[:900].replace(chr(10),' '))
    print()
