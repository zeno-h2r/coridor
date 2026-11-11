import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_OWNER').read().strip()
def post(path,body):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== register the uploaded .html file, then fetch via presigned URL ===")
for ext in ['html','svg']:
    try: key=open(f'/tmp/key_{ext}').read().strip()
    except: continue
    # try register shapes
    for body in [
      {"file":{"file_key":key,"name":f"zx-{ext}.{ext}","size":76,"type":"text/html"}},
      {"file":{"key":key,"name":f"zx-{ext}.{ext}","size":76,"type":"text/html"}},
    ]:
        c,b=post('/api/v1/files',body)
        print(f"  {ext} register -> {c} {b[:120].replace(chr(10),' ')}")
        if c in ('200','201'):
            try:
                f=json.loads(b)['files'][0]
                print(f"    file id={f['id']} name={f.get('name')} type={f.get('type')}")
                u=f.get('url') or ''
                print(f"    url_len={len(u)}")
                if u:
                    cmd=['curl','-s','-m','30','-i','-o','/tmp/ps','-w','%{http_code}',u]
                    cc=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
                    ps=open('/tmp/ps',encoding='utf-8',errors='replace').read()
                    ct=[l for l in ps.splitlines() if l.lower().startswith('content-type')]
                    print(f"    presigned GET -> {cc}  {ct[0] if ct else 'no CT'}")
                    print(f"    body: {ps.split(chr(10)+chr(10))[-1][:100]!r}")
            except Exception as e: print("    parse",e)
            break
