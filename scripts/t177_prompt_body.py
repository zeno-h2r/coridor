import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
R2=open('/tmp/r2_301').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or T),'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
base={"promptUri":"zx-probe/test","promptAttributes":{"a":"b"}}
for field in ['body','prompt','content','template','text','promptBody','promptText']:
    body={"ml_generative_prompt":dict(base,**{field:"ZXMARK {{7*7}}"})}
    c,b=req('POST','/api/v1/ml_generative_prompts',body,tok=R2)
    ok='  <<<< ACCEPTED' if c in ('200','201') else ''
    print(f"  +{field:12} -> {c} {b[:110].replace(chr(10),' ')}{ok}")
