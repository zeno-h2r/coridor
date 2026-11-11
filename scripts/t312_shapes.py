import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
T=open('/tmp/bac_OWNER').read().strip()
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','25','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+(tok or T),'-H',BB,'-H','Content-Type: application/json']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== schema leakage from 400s ===")
for p in ['/api/v1/generative/dynamic-schema','/api/v1/generative/batch-summaries',
          '/api/v1/assessments/1/run_scoring_agent','/api/v1/entities/1/migrate/run',
          '/api/v1/import_tools/validate','/api/v1/vendor_summary_reports/generate']:
    c,b=req('POST',p,{})
    print(f"\n  {c} {p}")
    print(f"    {b[:450].replace(chr(10),' ')}")
