import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
T=open('/tmp/bac_OWNER').read().strip()
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','90','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+(tok or T),'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== dynamic-schema with user_locale ===")
body={"fields":[{"name":"a","label":"A","type":"text"}],"context":"issue",
      "description":"ZX test schema","user_locale":"en-us"}
c,b=req('POST','/api/v1/generative/dynamic-schema',body)
print(f"  -> {c} {b[:600].replace(chr(10),' ')}")
print()
print("=== batch-summaries with rows ===")
for body in [{"promptAttributes":{"rows":[]}},
             {"promptAttributes":{"rows":[{"id":1,"text":"ZX"}]}},
             {"promptAttributes":{"rows":[{"id":1,"text":"ZX"}]},"promptUri":"template:controls/description"}]:
    c,b=req('POST','/api/v1/generative/batch-summaries',body)
    print(f"  {json.dumps(body)[:70]:72} -> {c}")
    print(f"      {b[:300].replace(chr(10),' ')}")
