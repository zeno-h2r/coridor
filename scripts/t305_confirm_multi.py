import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK={r:open(f'/tmp/bac_{r}').read().strip() for r in ['OWNER','SYSADMIN','REVIEWER','TESTER','EXTAUD']}
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','25','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== multiple objects: does the inversion hold? ===")
print(f"{'object':22} {'OWNER':>7} {'REVIEW':>7} {'TESTER':>7}")
for plural,rid,key in [('risks',1,'risk'),('risks',2,'risk'),('risks',3,'risk'),
                       ('narratives',31,'narrative'),('narratives',38,'narrative'),('narratives',39,'narrative')]:
    row=[]
    for r in ['OWNER','REVIEWER','TESTER']:
        c,b=req('PUT',f'/api/v1/{plural}/{rid}',{key:{"name":f"ZX-{r}-{uuid.uuid4().hex[:5]}"}},tok=TOK[r])
        row.append(c)
    print(f"{plural+'/'+str(rid):22} {row[0]:>7} {row[1]:>7} {row[2]:>7}")
print()
print("=== also check DELETE on the same resources ===")
print(f"{'object':22} {'OWNER':>7} {'REVIEW':>7} {'TESTER':>7}")
for plural,rid in [('risks',3),('narratives',39)]:
    row=[]
    for r in ['OWNER','REVIEWER','TESTER']:
        c,b=req('DELETE',f'/api/v1/{plural}/{rid}',tok=TOK[r])
        row.append(c)
    print(f"{plural+'/'+str(rid):22} {row[0]:>7} {row[1]:>7} {row[2]:>7}")
