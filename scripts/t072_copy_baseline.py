import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    code=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    b=open('/tmp/b',encoding='utf-8',errors='replace').read()
    return code,b
# 1. my own files
c,b=req('GET','/api/v1/files?page[size]=5')
print("files:",c,b[:600])
# 2. my issues
c,b=req('GET','/api/v1/issues?page[size]=5')
print("\nissues:",c,b[:500])
