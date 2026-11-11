import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TPU=open('/tmp/bac_TPU').read().strip()
def req(path,tok=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}',H+path,
         '-H','token: '+(tok or TPU),'-H',BB]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
for p in ['/api/v1/api_access_logs','/api/v1/role_permissions','/api/v1/brand_identities','/api/v1/dip_configurations','/api/v1/score_types','/api/v1/automation_workflows']:
    c,b=req(p)
    print(f"=== TPU {c} {p}  len={len(b)}")
    print("   ",b[:500].replace(chr(10),' '))
    print()
