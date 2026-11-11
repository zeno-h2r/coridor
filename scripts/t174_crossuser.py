import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
R2=open('/tmp/r2_301').read().strip()
def req(method,path,body=None,tok=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+(tok or T),'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== ml_traces / AI plane with role2 ===")
for p in ['/api/v1/ml_traces','/api/v1/ml_traces/count','/api/v2/ml-trace/1']:
    c,b=req('GET',p,tok=R2)
    print(f"  {c} {p}  {b[:180].replace(chr(10),' ')}")
print("\n=== cross-user assistant conversations (role2 vs owner) ===")
for uid in [235,230,231,1]:
    for label,tok in [("Owner",T),("SysAdm",R2)]:
        c,b=req('GET',f'/api/v1/assistant/conversations/conversation::user:{uid}',tok=tok)
        print(f"  {label:7} conv user {uid:3} -> {c} {b[:110].replace(chr(10),' ')}")
print("\n=== more log rows? pagination/filter ===")
for q in ['?page[size]=100','?filter[source_user_id][eq]=235','?page[number]=2']:
    c,b=req('GET','/api/v1/ml_generative_logs'+q,tok=R2)
    n=0
    try: n=len(json.loads(b).get('ml_generative_logs') or [])
    except: pass
    print(f"  {c} {q:38} rows={n}")
