import json,subprocess,os,sys
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(method,path,body=None,ct='application/json'):
    cmd=['curl','-s','-m','25','-o','/tmp/b','-w','%{http_code}','-X',method,H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: '+ct]
    if body is not None: cmd+=['-d',json.dumps(body)]
    code=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    try: b=open('/tmp/b',encoding='utf-8',errors='replace').read()
    except: b=''
    return code,b[:400]
targets=[
 ('GET','/api/v1/evidence-search/status',None),
 ('POST','/api/v1/evidence-search',{"resources":[{"resource_type":"issue","resource_id":1}],"user_instructions":"hi"}),
 ('GET','/api/v1/sox_ai_review',None),
 ('GET','/api/v1/sox_ai_review/queue',None),
 ('GET','/api/v1/webhook_urls',None),
 ('GET','/api/v1/table/export',None),
 ('POST','/api/v1/table/export',{"entities":"issues"}),
 ('POST','/api/v1/table/_op/async_export',{"entities":"issues"}),
 ('GET','/api/v1/processes/1',None),
 ('GET','/api/v1/amendments',None),
 ('GET','/api/v1/crosscomply',None),
 ('GET','/api/v1/teams',None),
 ('GET','/api/v1/tiering_rules',None),
 ('GET','/api/v1/mcp_tools',None),
 ('GET','/api/v1/usage/totals',None),
 ('GET','/api/v1/usage/top-users',None),
 ('GET','/api/v1/scores/latest',None),
 ('GET','/api/v1/threats/count',None),
 ('GET','/api/v1/auditable_entities/count',None),
 ('GET','/api/v1/auditable_entity_types/count',None),
 ('POST','/api/v1/ml-recommendations/init',{}),
 ('POST','/api/v1/ml-recommendations/match-by-text',{"text":"test"}),
 ('GET','/api/v1/ml-recommendations/files/generate_sample_file',None),
 ('POST','/api/v1/files/copy_files_to_fileable',{"file_ids":[1],"fileable_type":"Issue","fileable_id":1}),
 ('GET','/api/v1/regulatory-profiles/me',None),
 ('POST','/api/v1/regulatory-profiles/autofill',{}),
 ('GET','/api/v1/regulatory-signals/widget-metrics',None),
 ('GET','/api/v1/regulatory-signals/scoring-status',None),
 ('GET','/api/v1/sigma/health_check',None),
 ('GET','/api/v1/assistant_knowledge_files',None),
 ('GET','/api/v1/ui-schema.json',None),
 ('GET','/api/v1/ticketing/projects',None),
 ('GET','/api/v1/ticketing/ab_resource_types',None),
 ('GET','/api/v1/monitor-results/1/insights',None),
 ('GET','/api/v1/imported_third_parties/count',None),
 ('GET','/api/v1/ml_generative_prompts/count',None),
 ('GET','/api/v1/ml_generative_logs/count',None),
]
res=[]
for m,p,b in targets:
    c,txt=req(m,p,b)
    res.append({'m':m,'p':p,'code':c,'body':txt})
    print(f"{c} {m:5} {p}  {txt[:150].replace(chr(10),' ')}")
json.dump(res,open('state/t071_probe.json','w'),indent=1)
