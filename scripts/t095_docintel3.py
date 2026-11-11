import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','90','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
for fid,label in [(2692,'FOREIGN'),(2693,'OWN')]:
    c,b=req('POST','/api/v1/document_intelligence/attachment',
            {"attachableType":"Policy","attachableId":"1","fileId":fid,"file_id":fid})
    print(f"=== {label} file {fid}: {c}")
    print("   ",b[:600].replace(chr(10),' '))
    print()
