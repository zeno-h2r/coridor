import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
c,b=req('GET','/api/v1/vulnerability_import_runs')
print("list:",c,b[:500].replace(chr(10),' '))
print()
# try jobId-based lookups
for p in ['/api/v1/vulnerability_import_runs/31840','/api/v1/vms/schedules/31840',
          '/api/v1/vulnerability_import_runs?filter[job_id][eq]=31840',
          '/api/v1/vulnerability_import_runs/5/report']:
    c,b=req('GET',p)
    print(f"  {c} {p}  {b[:200].replace(chr(10),' ')}")
