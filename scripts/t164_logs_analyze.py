import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
R2=open('/tmp/tok301').read().strip()
def req(path,tok=None):
    cmd=['curl','-s','-m','40',H+path,'-H','token: '+(tok or T),'-H',BB]
    return subprocess.run(cmd,capture_output=True,text=True).stdout
d=json.loads(req('/api/v1/ml_generative_logs',tok=R2))
logs=d.get('ml_generative_logs') or []
print("log rows:",len(logs))
if logs:
    print("keys per row:",sorted(logs[0].keys()))
import re
allkeys=set()
for r in logs: allkeys|=set(r.keys())
print("\nunion of keys:",sorted(allkeys))
# look for sensitive content
blob=json.dumps(logs)
for kw in ['api_key','apikey','secret','token','password','bearer','sk-','AKIA','authorization','prompt','user_id','creator']:
    n=blob.lower().count(kw.lower())
    if n: print(f"  contains '{kw}': {n}")
print("\n--- sample row (trimmed) ---")
r=logs[0]
for k,v in r.items():
    s=str(v)
    print(f"  {k}: {s[:180]}")
