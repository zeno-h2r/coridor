import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TP=open('/tmp/bac_TPU').read().strip()
TO=open('/tmp/bac_SYSADMIN').read().strip()
def get(p,tok):
    cmd=['curl','-s','-m','25','-o','/tmp/b','-w','%{http_code}',H+p,'-H','token: '+tok,'-H',BB]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== TPU (role 11) direct API — the control ===")
for p in ['/api/v1/users','/api/v1/users/1','/api/v1/users/165','/api/v1/narratives/38']:
    c,b=get(p,TP)
    n=0
    try: n=len(json.loads(b).get('users') or [])
    except: pass
    print(f"  {c} {p:26} rows={n}  {b[:80].replace(chr(10),' ')}")
print()
print("=== SYSADMIN (role 2) direct API — for reference ===")
for p in ['/api/v1/users','/api/v1/users/1']:
    c,b=get(p,TO)
    n=0
    try: n=len(json.loads(b).get('users') or [])
    except: pass
    print(f"  {c} {p:26} rows={n}")
print()
print("=== the leaked data (from assistant) ===")
ents=json.load(open('/tmp/tpu_users.json'))
print(f"  records: {len(ents)}")
print(f"  shape: {json.dumps(ents[0])}")
print(f"  with email: {sum(1 for e in ents if e.get('description'))}")
