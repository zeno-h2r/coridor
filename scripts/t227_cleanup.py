import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TB=open('/tmp/tok_B-230').read().strip()
NID=open('/tmp/b_narr').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or TB),'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print(f"cleanup: delete narrative {NID} as its owner (230)")
c,b=req('DELETE',f'/api/v1/narratives/{NID}',tok=TB)
print(f"  DELETE -> {c} {b[:200].replace(chr(10),' ')}")
c,b=req('GET',f'/api/v1/narratives/{NID}',tok=TB)
print(f"  read after delete -> {c} {b[:120].replace(chr(10),' ')}")
