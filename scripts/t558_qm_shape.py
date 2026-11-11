import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TOK={r:open(f'/tmp/bac_{r}').read().strip() for r in ['OWNER','SYSADMIN','TESTER','TPU']}
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','90','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== complete the shape ===")
for body in [{"suggestable_type":"Narrative","suggestable_id":38},
             {"suggestable_type":"Narrative","id":38},
             {"suggestable_type":"Narrative","suggestable_id":"38"}]:
    c,b=req('POST','/api/v1/suggestions/query-matches',body,tok=TOK['OWNER'])
    print(f"  {json.dumps(body):56} -> {c} {b[:160].replace(chr(10),' ')}")
print()
print("=== role gating on the working shape ===")
body={"suggestable_type":"Narrative","suggestable_id":38}
for r in ['OWNER','SYSADMIN','TESTER','TPU']:
    c,b=req('POST','/api/v1/suggestions/query-matches',body,tok=TOK[r])
    n=0
    try:
        d=json.loads(b)
        for k in d:
            if isinstance(d[k],list): n=len(d[k])
    except: pass
    print(f"  {r:9} -> {c} items={n}  {b[:110].replace(chr(10),' ')}")
