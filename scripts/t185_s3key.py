import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(path,body,tok=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+(tok or T),'-H',BB,'-H','Content-Type: application/json','-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== vms/csv-import : s3Key shape probe ===")
c,b=req('/api/v1/vms/csv-import',{})
print(f"  empty -> {c} {b[:300].replace(chr(10),' ')}")
print("\n=== foreign S3 key (BUG-013 object the role cannot read) ===")
FOREIGN="demo-certs-dkim_demo/v1test/20/a21d2af0-ab9e-4d1e-b85b-552adc6caf1a/Sample 6 - 10.pdf"
for key in [FOREIGN,
            "demo-certs-dkim_demo/v1test/20/a21d2af0-ab9e-4d1e-b85b-552adc6caf1a/Sample%206%20-%2010.pdf",
            "shqa-playwright14991/demo/test/4633",
            "bugbounty1120509_qa/Attachment/11198/a3661eb1-3877-4a29-8b5c-e8f6160e22c1/zx-D-dnsfail.pdf"]:
    c,b=req('/api/v1/vms/csv-import',{"s3Key":key})
    print(f"  {key[:62]:64} -> {c} {b[:170].replace(chr(10),' ')}")
