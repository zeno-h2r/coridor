import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK={r:open(f'/tmp/bac_{r}').read().strip() for r in ['OWNER','SYSADMIN','REVIEWER','TESTER','EXTAUD','TPU']}
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','25','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== permission INversion: who holds risk:action.edit / narrative:action.edit ===")
print(f"{'role':10} {'risk PUT':>10} {'narr PUT':>10} {'ctrl PUT':>10}")
for r,tok in TOK.items():
    out=[]
    for plural,rid,key in [('risks',1,'risk'),('narratives',31,'narrative'),('controls',1,'control')]:
        c,b=req('PUT',f'/api/v1/{plural}/{rid}',{key:{"name":f"ZX-{r}-{uuid.uuid4().hex[:5]}"}},tok=tok)
        out.append(c)
    print(f"{r:10} {out[0]:>10} {out[1]:>10} {out[2]:>10}")
print()
print("=== cross-check against the RBAC matrix (BUG-018 data) ===")
c,b=req('GET','/api/v1/role_permissions?role_id=5',tok=TOK['OWNER'])
rp=json.loads(b)['role_permissions']
for key in ['risk:action.edit','narrative:action.edit','control:action.edit']:
    row=[x for x in rp if x.get('key')==key]
    print(f"  role5 {key:26} -> {[ (x.get('value'),x.get('section')) for x in row ] or 'NOT PRESENT'}")
