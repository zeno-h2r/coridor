import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TR2=open('/tmp/tok_R2-301').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or TR2),'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== bulk / mass delete paths for files ===")
for m,p,b in [
 ('DELETE','/api/v1/files',{"ids":[1,2,3]}),
 ('POST','/api/v1/files/bulk_delete',{"ids":[1,2,3]}),
 ('POST','/api/v1/files/bulk-destroy',{"ids":[1,2,3]}),
 ('DELETE','/api/v1/files/1,2,3',None),
 ('POST','/api/v1/files/_op/bulk_delete',{"ids":[1,2,3]}),
 ('DELETE','/api/v1/files/0',None),
]:
    c,t=req(m,p,b)
    mark='  <<<' if c in ('200','204') else ''
    print(f"  {c} {m:6} {p:34} {t[:110].replace(chr(10),' ')}{mark}")
