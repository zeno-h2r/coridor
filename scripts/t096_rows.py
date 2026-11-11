import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def post(path,body):
    cmd=['curl','-s','-m','90','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-AuditBoard-Source: SchemaTable Rows','-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
tests=[
 ("user", {"ab:query":{"entities":["user"],"filter":{},"include":["user"],"page":{"size":2}}}),
 ("user2",{"ab:query":{"entities":["user"],"filter":{},"pageSize":2}}),
 ("file", {"ab:query":{"entities":["file"],"filter":{"fileable_type":"Issue"},"include":["file"],"page":{"size":2}}}),
 ("issue",{"ab:query":{"entities":["issue"],"filter":{},"include":["issue"],"page":{"size":2}}}),
]
for n,b in tests:
    c,txt=post(f"/api/v1/table/query?entities={b['ab:query']['entities'][0]}",b)
    print(f"=== {n}: {c} len={len(txt)}")
    print("   ",txt[:700].replace(chr(10),' '))
    print()
