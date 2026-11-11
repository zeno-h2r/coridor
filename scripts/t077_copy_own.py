import json,subprocess,os,time
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None):
    cmd=['curl','-s','-m','40','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()

# copy MY file 2691 (bugbounty1120509_qa prefix) into issue 121
c,b=req('POST','/api/v1/files/copy_files_to_fileable',
        {"fileable_id":121,"fileable_type":"Issue","file_ids":[2691]})
print("COPY own 2691:",c)
try:
    d=json.loads(b); f=d['files'][0]
    print("  new id:",f.get('id'),"key:",f.get('key'))
    print("  meta:",json.dumps(f.get('meta')))
    open('/tmp/url_own','w').write(f.get('url') or '')
    open('/tmp/id_own','w').write(str(f.get('id')))
except Exception as e: print("err",e,b[:300])
