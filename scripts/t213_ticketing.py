import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== ticketing: what makes the 500 vs 404? ===")
for p in ['/api/v1/ticketing/tickets/1','/api/v1/ticketing/tickets/999999',
          '/api/v1/ticketing/users/1','/api/v1/ticketing/users/999999',
          '/api/v1/ticketing/tickets/types','/api/v1/ticketing/projects',
          '/api/v1/ticketing/ab_resource_types']:
    c,b=req('GET',p)
    print(f"  {c} {p:44} {b[:130].replace(chr(10),' ')}")
print("\n=== ticketing POST shapes (create/link) ===")
for p,b in [('/api/v1/ticketing/tickets',{}),
            ('/api/v1/ticketing/tickets',{"ticket":{"title":"zx","description":"zx"}}),
            ('/api/v1/ticketing/tickets/link',{}),
            ('/api/v1/ticketing/tickets/bulk',{"tickets":[]})]:
    c,t=req('POST',p,b)
    print(f"  {c} POST {p:40} {t[:160].replace(chr(10),' ')}")
