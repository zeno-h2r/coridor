import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TA=open('/tmp/tok_A-231').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','45','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or TA),'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
# enumerate real ids first
def ids(ent):
    c,b=req('POST',f'/api/v1/table/query?entities={ent}',
            {"ab:query":{"entities":[ent],"filter":{},"include":[ent]}})
    try: return [i['id'] for i in (json.loads(b).get('included') or [])][:3]
    except: return []
print("=== DELETE verb sweep on other resources (A=Owner) ===")
for ent in ['attachment','document_version','timesheet_entry','markup_sample',
            'esg_metric_value','webhook_url','brand_identity','user_skill',
            'api_access_log','recurring_schedule']:
    rid=ids(ent)
    if not rid:
        print(f"  {ent:22} no ids"); continue
    for i in rid[:1]:
        plural=ent+'s' if not ent.endswith('s') else ent
        c,b=req('DELETE',f'/api/v1/{plural}/{i}',tok=TA)
        mark='  <<< DELETE OK' if c in ('200','204') else ''
        print(f"  {ent:22} id={i:<6} DELETE -> {c} {b[:80].replace(chr(10),' ')}{mark}")
