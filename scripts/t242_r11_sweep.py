import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TR=open('/tmp/tok_R11-315').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','45','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or TR),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== role-11 (limited Third Party User) vs Owner content ===")
print(f"{'endpoint':46} {'GET':>5} {'PUT':>5} {'DELETE':>7}")
targets=[
 ('narrative','/api/v1/narratives/67','narrative'),
 ('issue','/api/v1/issues/121','issue'),
 ('control','/api/v1/controls/1','control'),
 ('risk','/api/v1/risks/1','risk'),
 ('file','/api/v1/files/2728','file'),
 ('attachment','/api/v1/attachments/11214','attachment'),
 ('document_version','/api/v1/document_versions/1402','document_version'),
 ('user','/api/v1/users/230','user'),
]
for label,base,key in targets:
    g,_=req('GET',base,tok=TR)
    p,pb=req('PUT',base,{key:{"name":"ZX-R11-PROBE"}},tok=TR)
    d,_=req('DELETE',base,tok=TR)
    note=''
    if g=='200': note='READ'
    if p=='200': note+=' EDIT!'
    if d in ('200','204'): note+=' DELETE!'
    print(f"{label:20} {base[:24]:26} {g:>5} {p:>5} {d:>7}  {note}")
