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
tag='ZXB'+uuid.uuid4().hex[:5]
tests=[
 ('plain', f'ZX{tag}'),
 ('lt-only', f'<ZX{tag}'),
 ('gt-only', f'ZX>{tag}'),
 ('lt-gt', f'<b>ZX{tag}</b>'),
 ('img', f'<img src=x>ZX{tag}'),
 ('svg', f'<svg>ZX{tag}</svg>'),
 ('script', f'<script>ZX{tag}</script>'),
 ('onerror', f'ZX onerror=alert(1) {tag}'),
 ('quote', f'"ZX{tag}'),
 ('brace', f'{{{{7*7}}}}ZX{tag}'),
 ('dollar', f'${{7*7}}ZX{tag}'),
 ('semicolon', f';id;ZX{tag}'),
 ('dotdot', f'../../etc/passwd{tag}'),
 ('percent', f'%s%sZX{tag}'),
]
print(f"{'case':12} {'code':>5}  stored")
for label,pay in tests:
    c,b=call('POST','/api/v1/risks',{"risk":{"name":pay}})
    stored=''
    if c in ('200','201'):
        try: stored=repr(json.loads(b)['risks'][0].get('name'))[:60]
        except: stored=b[:60]
    else:
        try: stored=json.loads(b).get('errors',[{}])[0].get('detail','')[:60]
        except: stored=b[:60]
    print(f"{label:12} {c:>5}  {stored}")
