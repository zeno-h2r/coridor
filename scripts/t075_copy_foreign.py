import json,subprocess,os,sys
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None,extra=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if extra:
        for k,v in extra.items(): cmd+=['-H',f'{k}: {v}']
    if body is not None: cmd+=['-d',json.dumps(body)]
    code=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return code,open('/tmp/b',encoding='utf-8',errors='replace').read()

# baseline: what does a foreign file member route return (BUG-013 recheck on 47.3)
for fid in [735, 2691, 2000]:
    c,b=req('GET',f'/api/v1/files/{fid}')
    print(f"GET /files/{fid} -> {c} {b[:260]}")
print()
# copy foreign file into issue 121
c,b=req('POST','/api/v1/files/copy_files_to_fileable',
        {"fileable_id":121,"fileable_type":"Issue","file_ids":[735]})
print("COPY 735 -> Issue 121:",c,b[:800])
