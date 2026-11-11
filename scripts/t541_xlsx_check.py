import json,subprocess,os,zipfile,io
H=os.environ['H']; BB=os.environ['BB']
for field in ['description','altText','function','phase']:
    try: url=open(f'/tmp/flow_{field}').read().strip()
    except: continue
    subprocess.run(['curl','-s','-m','60','-o',f'/tmp/f_{field}.xlsx',url])
    p=f'/tmp/f_{field}.xlsx'
    if not os.path.exists(p): print(f"  {field}: no file"); continue
    d=open(p,'rb').read()
    print(f"\n=== {field}: {len(d)} bytes, magic={d[:4]}")
    try:
        z=zipfile.ZipFile(io.BytesIO(d))
        names=z.namelist()
        print(f"  entries: {len(names)}")
        blob=b''
        for n in names:
            if n.endswith('.xml'): blob+=z.read(n)
        txt=blob.decode('utf-8',errors='replace')
        print(f"  contains 'onerror': {'onerror' in txt}")
        print(f"  contains '<img': {'<img' in txt}")
        print(f"  contains '&lt;img': {'&lt;img' in txt}")
        import re
        m=re.findall(r'ZXF[0-9a-f]{5}', txt)
        print(f"  tag found: {set(m)}")
        # show context around tag
        i=txt.find('ZXF')
        if i>0: print(f"  context: {txt[max(0,i-120):i+60]!r}")
    except Exception as e:
        print(f"  not a zip: {e}  head={d[:80]}")
