import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(path,body):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-AuditBoard-Source: SchemaTable Rows','-d',json.dumps(body)]
    code=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return code,open('/tmp/b',encoding='utf-8',errors='replace').read()
tests=[
 ('file',{"ab:query":{"entities":["file"],"filter":{}}}),
 ('file_ver',{"ab:query":{"entities":["file_version"],"filter":{}}}),
 ('issue',{"ab:query":{"entities":["issue"],"filter":{}}}),
 ('user',{"ab:query":{"entities":["user"],"filter":{}}}),
]
for name,b in tests:
    c,txt=req('/api/v1/table/query?entities='+b['ab:query']['entities'][0],b)
    print(f"--- {name}: {c} len={len(txt)}")
    print(txt[:700].replace(chr(10),' '))
    print()
