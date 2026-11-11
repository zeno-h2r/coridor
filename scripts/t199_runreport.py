import json,subprocess,os,time
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
for rid in [3,4,5]:
    for suffix in ['/report','']:
        c,b=req('GET',f'/api/v1/vulnerability_import_runs/{rid}{suffix}')
        print(f"  run {rid}{suffix or ' (bare)'}: {c} {b[:300].replace(chr(10),' ')}")
print()
# table DSL for the run plane
c,b=req('POST','/api/v1/table/query?entities=vulnerability_import_run',
        {"ab:query":{"entities":["vulnerability_import_run"],"filter":{},"include":["vulnerability_import_run"]}})
print("table/query runs:",c)
try:
    d=json.loads(b); inc=d.get('included') or []
    print("  rows:",len(inc))
    for r in inc[-5:]:
        a=r.get('attributes') or {}
        print("   ",r['id'],a.get('status'),str(a.get('errorMessage') or a.get('error') or '')[:160])
except Exception as e: print("  ",b[:300])
