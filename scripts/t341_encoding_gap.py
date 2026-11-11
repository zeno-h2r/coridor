import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_OWNER').read().strip()
def call(m,p,body=None):
    cmd=['curl','-s','-m','25','-o','/tmp/hb','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/hb',encoding='utf-8',errors='replace').read()
tag='ZXG'+uuid.uuid4().hex[:5]
print("=== which resource families entity-encode on write? ===")
# create one object per family with a benign <b> probe, then read back
probes=[
 ('risks','risk',{'name':f'<b>ZX{tag}</b>'}),
 ('narratives','narrative',{'name':f'<b>ZX{tag}</b>','uid':f'zx{tag}'}),
 ('teams','team',{'name':f'<b>ZX{tag}</b>'}),
 ('controls','control',{'name':f'<b>ZX{tag}</b>'}),
 ('auditable_entities','auditable_entity',{'name':f'<b>ZX{tag}</b>'}),
 ('esg_metrics','esg_metric',{'name':f'<b>ZX{tag}</b>'}),
]
for plural,key,body in probes:
    c,b=call('POST',f'/api/v1/{plural}',{key:body})
    if c in ('200','201'):
        try:
            o=json.loads(b)[plural][0]
            nm=o.get('name')
            enc = '&lt;' in str(nm)
            print(f"  {plural:22} id={o['id']:<5} ENCODED={enc}  stored={str(nm)[:50]!r}")
        except Exception as e:
            print(f"  {plural:22} {c} parse-err")
    else:
        try: d=json.loads(b).get('errors',[{}])[0].get('detail','')[:70]
        except: d=b[:70]
        print(f"  {plural:22} {c} {d}")
