import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
R2=open('/tmp/r2_301').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or T),'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== A. create ml_generative_prompt, camelCase ===")
for body in [
 {"ml_generative_prompt":{"promptUri":"zx-probe/test","promptAttributes":{},"promptUriByName":"zx"}},
 {"mlGenerativePrompt":{"promptUri":"zx-probe/test","promptAttributes":{}}},
 {"promptUri":"zx-probe/test","promptAttributes":{},"promptUriByName":"zx"},
]:
    c,b=req('POST','/api/v1/ml_generative_prompts',body,tok=R2)
    print(f"  {json.dumps(body)[:78]:80} -> {c} {b[:140].replace(chr(10),' ')}")
print("\n=== B. create ml_generative_log with XSS marker (stored XSS test) ===")
XSS='<img src=x onerror=alert(document.domain)>ZXMARK'
for body in [
 {"ml_generative_log":{"generated_output":XSS,"context":{},"version_context":{}}},
 {"mlGenerativeLog":{"generatedOutput":XSS,"context":{},"versionContext":{}}},
 {"generatedOutput":XSS,"context":{},"versionContext":{}},
]:
    c,b=req('POST','/api/v1/ml_generative_logs',body,tok=R2)
    print(f"  {json.dumps(body)[:78]:80} -> {c} {b[:160].replace(chr(10),' ')}")
print("\n=== C. read logs back, is marker stored + escaped? ===")
c,b=req('GET','/api/v1/ml_generative_logs',tok=R2)
print(f"  {c} len={len(b)}")
print(f"  contains ZXMARK: {'ZXMARK' in b}")
print(f"  contains raw <img: {'<img' in b}")
print(f"  contains &lt;img: {'&lt;img' in b}")
