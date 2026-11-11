import json,subprocess,os,uuid
from concurrent.futures import ThreadPoolExecutor
H=os.environ['H']; BB=os.environ['BB']
TOK={r:open(f'/tmp/bac_{r}').read().strip() for r in ['OWNER','SYSADMIN','REVIEWER','TESTER','EXTAUD','TPU']}
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','25','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
def getfield(res,rid,field,tok):
    c,b=req('GET',f'/api/v1/{res}/{rid}',tok=tok)
    try:
        d=json.loads(b); arr=d.get(res) or d.get(res.rstrip('s')) or []
        return arr[0].get(field) if arr else None
    except: return None
# resource -> (path plural, key, editable field)
CASES=[
 ('issues',121,'issue','title'),
 ('controls',1,'control','name'),
 ('risks',1,'risk','name'),
 ('narratives',31,'narrative','name'),
]
print(f"{'resource':12} {'id':>4} {'field':8} " + " ".join(f"{r[:6]:>6}" for r in TOK))
for plural,rid,key,field in CASES:
    row=[]
    for r,tok in TOK.items():
        uniq=f"ZX-{r}-{uuid.uuid4().hex[:6]}"
        c,b=req('PUT',f'/api/v1/{plural}/{rid}',{key:{field:uniq}},tok=tok)
        after=getfield(plural,rid,field,tok)
        landed = (after==uniq)
        row.append(f"{'LAND' if landed else c:>6}")
    print(f"{plural:12} {rid:>4} {field:8} " + " ".join(row))
