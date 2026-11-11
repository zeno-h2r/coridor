import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
for p in ['/api/v1/attachments/11200','/api/v1/attachments/11199','/api/v1/attachments?filter[id][eq]=11200','/api/v1/attachments/html/11200']:
    c,b=req('GET',p)
    print(f"{c} GET {p}")
    print("   ",b[:400].replace(chr(10),' '))
