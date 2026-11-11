import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def get(path):
    cmd=['curl','-s','-m','40',H+path,'-H','token: '+T,'-H',BB]
    return subprocess.run(cmd,capture_output=True,text=True).stdout
for fid in [2691,2693,2692]:
    b=get(f'/api/v1/files/{fid}')
    try:
        f=json.loads(b)['files'][0]
        u=f.get('url') or ''
        print(f"--- {fid} name={f.get('name')} size={f.get('size')} url_len={len(u)}")
        print("    key:",f.get('key'))
        if u: open(f'/tmp/u{fid}','w').write(u)
    except Exception as e: print(fid,"err",b[:200])
