import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def post(path,body):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-AuditBoard-Source: SchemaTable Rows','-d',json.dumps(body)]
    code=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return code,open('/tmp/b',encoding='utf-8',errors='replace').read()
c,txt=post('/api/v1/table/query?entities=file',{"ab:query":{"entities":["file"],"filter":{}}})
d=json.loads(txt)
rows=d['data']
ids=[int(r['id']) for r in rows]
print("file rows:",len(rows),"id range:",min(ids),"-",max(ids))
print("meta:",json.dumps(d.get('meta'))[:300])
json.dump(ids,open('state/file_ids.json','w'))
# also get my issues
c,txt=post('/api/v1/table/query?entities=issue',{"ab:query":{"entities":["issue"],"filter":{}}})
d=json.loads(txt)
iids=[int(r['id']) for r in d['data']]
print("issue rows:",len(iids),"range:",min(iids),"-",max(iids))
json.dump(iids,open('state/issue_ids.json','w'))
