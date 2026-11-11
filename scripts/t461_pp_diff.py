import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
def get(p,tok):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}',H+p,'-H','token: '+tok,'-H',BB]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
def ids(r):
    tok=open(f'/tmp/bac_{r}').read().strip()
    c,b=get('/api/v1/project_plans',tok)
    try: return {x['id'] for x in json.loads(b)['project_plans']}
    except: return set()
o=ids('OWNER'); t=ids('TESTER'); p=ids('TPU')
print(f"OWNER={len(o)} TESTER={len(t)} TPU={len(p)}")
print(f"TESTER-only (not visible to OWNER): {sorted(t-o)}")
print(f"OWNER-only (not visible to TESTER): {sorted(o-t)}")
print(f"TPU sees: {sorted(p)}")
print()
print("=== what are the Tester-only plans? ===")
tok=open('/tmp/bac_TESTER').read().strip()
c,b=get('/api/v1/project_plans',tok)
d=json.loads(b)['project_plans']
for x in d:
    if x['id'] in (t-o):
        print(f"  id={x['id']} name={str(x.get('name'))[:40]!r} start={x.get('start_date')} end={x.get('end_date')}")
        print(f"    perms={json.dumps(x.get('_permissions'))}")
print()
print("=== and the TPU-visible ones? ===")
tok=open('/tmp/bac_TPU').read().strip()
c,b=get('/api/v1/project_plans',tok)
for x in json.loads(b)['project_plans']:
    print(f"  id={x['id']} name={str(x.get('name'))[:40]!r} perms={json.dumps(x.get('_permissions'))[:70]}")
