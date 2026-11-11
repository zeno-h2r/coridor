import json,subprocess,os,time
H=os.environ['H']; BB=os.environ['BB']
T=open('/tmp/bac_OWNER').read().strip()
def ds(desc="ZX"):
    body={"fields":[{"name":"a","label":"A","type":"text"}],"context":"issue",
          "description":desc,"user_locale":"en-us"}
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X','POST',
         H+'/api/v1/generative/dynamic-schema',
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== is the AI endpoint locked out or just rate limited? ===")
for i in range(3):
    c,b=ds()
    print(f"  attempt {i+1}: {c} {b[:200]}")
    time.sleep(20)
