import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
R2=open('/tmp/r2_301').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or T),'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== POST ml_generative_prompts/count (both roles) ===")
for label,tok in [("Owner",T),("SysAdmin",R2)]:
    c,b=req('POST','/api/v1/ml_generative_prompts/count',{},tok=tok)
    print(f"  {label:9} -> {c} {b[:200].replace(chr(10),' ')}")
print("\n=== POST assistant_knowledge_files {files:[{file_id}]} (SysAdmin) ===")
c,b=req('POST','/api/v1/assistant_knowledge_files',{"files":[{"file_id":2691}]},tok=R2)
print(f"  -> {c} {b[:500].replace(chr(10),' ')}")
print("\n=== same as Owner (control) ===")
c,b=req('POST','/api/v1/assistant_knowledge_files',{"files":[{"file_id":2691}]},tok=T)
print(f"  -> {c} {b[:300].replace(chr(10),' ')}")
print("\n=== list after write (SysAdmin) ===")
c,b=req('GET','/api/v1/assistant_knowledge_files',tok=R2)
print(f"  -> {c} {b[:600].replace(chr(10),' ')}")
