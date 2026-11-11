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
print("=== why did OWNER get 422 on risks/1 and narratives/31? ===")
for plural,rid,key in [('risks',1,'risk'),('narratives',31,'narrative')]:
    c,b=req('PUT',f'/api/v1/{plural}/{rid}',{key:{"name":f"ZX-{uuid.uuid4().hex[:6]}"}},tok=TOK['OWNER'])
    print(f"\n  OWNER PUT {plural}/{rid} -> {c}")
    print(f"    {b[:400].replace(chr(10),' ')}")
print("\n=== current state of those objects ===")
for plural,rid in [('risks',1),('narratives',31),('controls',1)]:
    c,b=req('GET',f'/api/v1/{plural}/{rid}',tok=TOK['OWNER'])
    try:
        arr=json.loads(b).get(plural) or []
        o=arr[0] if arr else {}
        print(f"  {plural}/{rid}: name={o.get('name')!r} updated={o.get('updated_at')}")
    except Exception as e: print(f"  {plural}/{rid}: {c} {b[:100]}")
