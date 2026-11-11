import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TA=open('/tmp/tok_A').read().strip()
TB=open('/tmp/tok_B').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','45','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or TA),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
# resources where B may own something; test A's edit/delete
targets=[
 ('narrative',67),('issue',121),('control',1),('risk',1),('auditee',92),
 ('auditable_entity',92),('framework',1),('policy',1),('process',1),
 ('test',1),('ops_audit_item',1),('document',1),('attachment',11208),
 ('file',2712),('esg_metric',1),('vendor',1),('exception_request',1),
]
print(f"{'resource':22} {'id':>6} {'GET':>5} {'PUT':>5} {'DELETE':>7}  detail")
for res,tid in targets:
    plural = res if res.endswith('s') else res+'s'
    base=f'/api/v1/{plural}/{tid}'
    g,_=req('GET',base,tok=TA)
    p,pb=req('PUT',base,{res:{"name":"ZX-BAC-PROBE"}},tok=TA)
    d,db=req('DELETE',base,tok=TA)
    det=''
    if p=='200': det='<<< EDIT ALLOWED'
    elif d in ('200','204'): det='<<< DELETE ALLOWED'
    elif p=='422':
        try: det=json.loads(pb)['errors'][0].get('detail','')[:60]
        except: det=pb[:60]
    print(f"{res:22} {tid:>6} {g:>5} {p:>5} {d:>7}  {det}")
