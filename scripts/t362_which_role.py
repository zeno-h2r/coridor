import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
def get(p,tok):
    cmd=['curl','-s','-m','25','-o','/tmp/b','-w','%{http_code}',H+p,'-H','token: '+tok,'-H',BB]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== which role can view exception 32? ===")
for r in ['OWNER','SYSADMIN','TESTER']:
    try: tok=open(f'/tmp/bac_{r}').read().strip()
    except: continue
    c,b=get('/api/v1/exception_requests/32',tok)
    print(f"  {r:9} {c}  {b[:110].replace(chr(10),' ')}")
print()
print("=== can any role LIST exceptions? ===")
for r in ['OWNER','SYSADMIN','TESTER']:
    try: tok=open(f'/tmp/bac_{r}').read().strip()
    except: continue
    c,b=get('/api/v1/exception_requests',tok)
    n=0
    try: n=len(json.loads(b).get('exception_requests') or [])
    except: pass
    print(f"  {r:9} {c} rows={n}  {b[:90].replace(chr(10),' ')}")
