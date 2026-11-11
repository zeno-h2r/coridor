import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
R2=open('/tmp/r2_301').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or T),'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== ml_generative_prompts: READ shape ===")
for p in ['/api/v1/ml_generative_prompts','/api/v1/ml_generative_prompts?page[size]=50']:
    c,b=req('GET',p,tok=R2)
    print(f"  {c} {p} len={len(b)}")
    print("   ",b[:400].replace(chr(10),' '))
print("\n=== CREATE a prompt (write test) ===")
c,b=req('POST','/api/v1/ml_generative_prompts',
        {"ml_generative_prompt":{"prompt_uri":"zx-probe/test","prompt_attributes":{},"body":"ZXMARK"}},tok=R2)
print(f"  {c} {b[:500].replace(chr(10),' ')}")
print("\n=== assistant_knowledge_files: create ===")
c,b=req('POST','/api/v1/assistant_knowledge_files',
        {"assistant_knowledge_file":{"name":"zx-probe","file_id":2691}},tok=R2)
print(f"  {c} {b[:400].replace(chr(10),' ')}")
