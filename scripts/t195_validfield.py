import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
for rt in ['vulnerabilityFinding','auditableEntity']:
    c,b=req('GET',f'/api/v1/asset_match_mappings/auditboard_fields?resource_type={rt}')
    print(f"=== {c} resource_type={rt}")
    print("   ",b[:700].replace(chr(10),' '))
    print()
c,b=req('GET','/api/v1/field_mappings/configuration?auditboardResourceType=vulnerabilityFinding')
print(f"=== {c} field_mappings/configuration")
print("   ",b[:700].replace(chr(10),' '))
