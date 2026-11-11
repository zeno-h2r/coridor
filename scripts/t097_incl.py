import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def post(path,body):
    cmd=['curl','-s','-m','90','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-AuditBoard-Source: SchemaTable Rows','-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
c,txt=post('/api/v1/table/query?entities=file',{"ab:query":{"entities":["file"],"filter":{"fileable_type":"Issue"},"include":["file"],"page":{"size":2}}})
d=json.loads(txt)
print("keys:",list(d.keys()))
inc=d.get('included')
print("included count:",len(inc) if inc else 0)
if inc:
    print(json.dumps(inc[0],indent=1)[:1200])
