import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TO=open('/tmp/bac_OWNER').read().strip()
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-AuditBoard-Source: SchemaTable Rows','-H','Accept: text/csv, application/msexcel']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== export with header as array of column objects ===")
shapes=[
 {"ab:query":{"entities":["user"],"filter":{}},
  "ab:export":{"header":["email","fullName"],"format":"csv","timezone":"UTC","fileName":"zx"}},
 {"ab:query":{"entities":["user"],"filter":{}},
  "ab:export":{"header":[{"key":"email","label":"Email"},{"key":"fullName","label":"Name"}],
               "format":"csv","timezone":"UTC","fileName":"zx"}},
 {"ab:query":{"entities":["user"],"filter":{}},
  "ab:export":{"header":{"email":"Email","fullName":"Name"},"format":"csv","timezone":"UTC","fileName":"zx"}},
]
for s in shapes:
    c,b=req('POST','/api/v1/table/export?entities=user',s,tok=TO)
    print(f"\n  header={json.dumps(s['ab:export']['header'])[:60]}")
    print(f"    -> {c} {b[:220].replace(chr(10),' ')}")
print()
print("=== what columns does the user table expose? ===")
c,b=req('POST','/api/v1/table/query?entities=user',
        {"ab:query":{"entities":["user"],"filter":{},"include":["user"]}},tok=TO)
try:
    d=json.loads(b); inc=d.get('included') or []
    if inc: print("  attrs:",sorted((inc[0].get('attributes') or {}).keys())[:25])
    print("  schema:",json.dumps(d.get('meta',{}).get('schema'))[:300])
except Exception as e: print("  ",c,b[:200])
