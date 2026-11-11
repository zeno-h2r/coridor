import json,subprocess,os,time
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
for attempt in range(4):
    print(f"--- poll {attempt+1} ---")
    for rid in [3,4,5]:
        c,b=req('GET',f'/api/v1/vulnerability_import_runs/{rid}')
        print(f"  run {rid}: {c} {b[:260].replace(chr(10),' ')}")
    c,b=req('GET','/api/v1/vulnerability_import_runs')
    if c=='200':
        try:
            runs=json.loads(b).get('vulnerability_import_runs') or []
            print("  all runs:",[(r.get('id'),r.get('status')) for r in runs][-6:])
        except: pass
    if attempt<3: time.sleep(12)
