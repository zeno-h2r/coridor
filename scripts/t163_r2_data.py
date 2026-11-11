import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
R2=open('/tmp/tok301').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or T),'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
for p in ['/api/v1/assistant_knowledge_files','/api/v1/ml_generative_prompts','/api/v1/ml_generative_prompts/count','/api/v1/ml_generative_logs']:
    c,b=req('GET',p,tok=R2)
    print(f"=== {c} GET {p}  len={len(b)}")
    print("   ",b[:700].replace(chr(10),' '))
    print()
