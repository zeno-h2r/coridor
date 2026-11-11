import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']; WH=os.environ['WH']
def req(body):
    cmd=['curl','-s','-m','90','-o','/tmp/b','-w','%{http_code}','-X','POST',
         H+'/api/v1/attachments/html',
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json','-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
base={"html":"<h1>zx</h1>","type":"pdf","attachableType":"Narrative","attachableId":"1","fileName":"zx"}
c,b=req(base)
print("baseline:",c,b[:400])
