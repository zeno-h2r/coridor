import json,subprocess,os,uuid,zipfile,io
H=os.environ['H']; BB=os.environ['BB']
TP=open('/tmp/bac_TPU').read().strip()
TO=open('/tmp/bac_OWNER').read().strip()
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='ZXL'+uuid.uuid4().hex[:5]
node=[{"id":"1","description":f"ZX{tag}","nextStep":[],"connectorLabel":[],
       "shapeType":"Process","function":"","phase":"","altText":""}]
print("=== TPU generates a flowchart, capture URL ===")
c,b=req('POST','/api/v1/documents/flowchart',node,tok=TP)
print(f"  {c}")
url=json.loads(b).get('url','') if c=='200' else ''
print(f"  url_len={len(url)}")
if url:
    key=url.split('.amazonaws.com/')[1].split('?')[0]
    print(f"  key={key}")
    open('/tmp/tpu_flow_url','w').write(url)
    # can OWNER fetch TPU's generated file?
    subprocess.run(['curl','-s','-m','40','-o','/tmp/tpu_flow.xlsx','-w','%{http_code}',url])
    d=open('/tmp/tpu_flow.xlsx','rb').read()
    print(f"  fetch as anyone (presigned): {len(d)} bytes magic={d[:4]}")
    print(f"  contains tag: {tag.encode() in d}")
print()
print("=== does TPU's flowchart appear in the tenant file list? ===")
for r,tok in [('TPU',TP),('OWNER',TO)]:
    c,b=req('POST','/api/v1/table/query?entities=file',
            {"ab:query":{"entities":["file"],"filter":{},"include":["file"]}},tok=tok)
    n=0; hit=False
    try:
        inc=json.loads(b).get('included') or []
        n=len(inc)
        hit=any(tag in str((f.get('attributes') or {}).get('name','')) for f in inc)
    except: pass
    print(f"  {r:9} files={n} contains_flowchart_tag={hit}")
