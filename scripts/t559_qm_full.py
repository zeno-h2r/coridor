import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TOK={r:open(f'/tmp/bac_{r}').read().strip() for r in ['OWNER','SYSADMIN','TESTER','TPU']}
def req(body,tok):
    cmd=['curl','-s','-m','120','-o','/tmp/b','-w','%{http_code}','-X','POST',
         H+'/api/v1/suggestions/query-matches',
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== full shape ===")
body={"suggestable_type":"Narrative","suggestable_id":38,"suggested_type":"ControlsDatum"}
c,b=req(body,TOK['OWNER'])
print(f"  OWNER -> {c}")
print(f"  {b[:400].replace(chr(10),' ')}")
print()
print("=== role gating ===")
for r in ['OWNER','SYSADMIN','TESTER','TPU']:
    c,b=req(body,TOK[r])
    n=0; keys=[]
    try:
        d=json.loads(b)
        keys=list(d.keys())
        for k in d:
            if isinstance(d[k],list): n=len(d[k])
    except: pass
    print(f"  {r:9} -> {c} rows={n} keys={keys[:5]}  {b[:90].replace(chr(10),' ')}")
