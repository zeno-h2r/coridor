import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_OWNER').read().strip()
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+(tok or TOK),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='ZXK'+uuid.uuid4().hex[:5]
PROBE=f'<b>{tag}</b>'
print("=== JSON blobs with allowlisted <b>: encoded or raw? ===")
for res,rid,key in [('risks',1,'risk'),('controls',1,'control'),('exception_requests',33,'exception_request')]:
    for f in ['custom_json1','formula_data','field_data','reference_meta']:
        body={key:{f:{"zx":PROBE}}}
        c,b=req('PUT',f'/api/v1/{res}/{rid}',body)
        if c!='200':
            print(f"  {res}/{rid}.{f:14} PUT={c}")
            continue
        c2,b2=req('GET',f'/api/v1/{res}/{rid}')
        st=None
        try:
            arr=json.loads(b2).get(res) or []
            st=arr[0].get(f) if arr else None
        except: pass
        s=json.dumps(st)
        print(f"  {res}/{rid}.{f:14} PUT=200 stored={s[:90]}")
        print(f"        RAW={'<b>' in s}  ENCODED={'&lt;b&gt;' in s}")
