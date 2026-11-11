import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK={r:open(f'/tmp/bac_{r}').read().strip() for r in ['OWNER','SYSADMIN','TESTER','TPU']}
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== suggestions/query-matches : shape + role gating ===")
for p in ['/api/v1/suggestions/query-matches?id=38','/api/v1/suggestions/query-matches?narrative_id=38',
          '/api/v1/suggestions/query-matches?narrativeId=38']:
    c,b=req('GET',p,tok=TOK['OWNER'])
    print(f"  OWNER {c} {p:52} {b[:130].replace(chr(10),' ')}")
print()
print("=== POST shape ===")
for body in [{"id":38},{"narrativeId":38},{"narrative_id":38},{"id":38,"limit":5}]:
    c,b=req('POST','/api/v1/suggestions/query-matches',body,tok=TOK['OWNER'])
    print(f"  {json.dumps(body):34} -> {c} {b[:130].replace(chr(10),' ')}")
print()
print("=== role gating on the working shape ===")
for r in ['OWNER','SYSADMIN','TESTER','TPU']:
    c,b=req('GET','/api/v1/suggestions/query-matches?id=38',tok=TOK[r])
    print(f"  {r:9} -> {c} {b[:100].replace(chr(10),' ')}")
