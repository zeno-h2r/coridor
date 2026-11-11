import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
T=open('/tmp/bac_OWNER').read().strip()
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+(tok or T),'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== dynamic-schema: full required fields ===")
c,b=req('POST','/api/v1/generative/dynamic-schema',{})
try:
    d=json.loads(b)
    print("  required:",[x['path'] for x in d.get('details',[])])
except: print("  ",b[:300])
print()
print("=== attempt valid dynamic-schema ===")
body={"fields":[{"name":"a","label":"A","type":"text"}],"context":"issue","description":"ZX test"}
c,b=req('POST','/api/v1/generative/dynamic-schema',body)
print(f"  -> {c} {b[:400].replace(chr(10),' ')}")
print()
print("=== batch-summaries with promptAttributes ===")
for body in [{"promptAttributes":{}},
             {"promptAttributes":{"a":"b"}},
             {"promptAttributes":{},"promptUri":"template:controls/description"}]:
    c,b=req('POST','/api/v1/generative/batch-summaries',body)
    print(f"  {json.dumps(body)[:60]:62} -> {c} {b[:220].replace(chr(10),' ')}")
